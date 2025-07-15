<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-end">
      <Button
        ref="closeButton"
        icon="x"
        variant="ghost"
        class="h-6 w-6 p-0"
        @click="closeBox"
      />
    </div>

    <div class="flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <div class="flex-1">
          <textarea
            ref="messageInput"
            v-model="message"
            class="w-full min-h-[120px] bg-white rounded-lg border border-gray-200 p-3 resize-none"
            placeholder="Type your message here..."
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="message += '\n'"
          />
        </div>
      </div>
    </div>
    <div class="flex justify-end gap-2">
      <Button 
        variant="ghost" 
        @click="closeBox"
      >
        {{ __('Cancel') }}
      </Button>
      <Button
        ref="sendButton"
        variant="solid"
        :loading="sendMessageResource.loading"
        @click="sendMessage"
      >
        {{ __('Send') }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { createResource, Button } from 'frappe-ui'

// Props
const props = defineProps({
  contact: {
    type: Object,
    required: true,
    default: () => ({ doctype: 'CRM Lead', name: '', mobile_no: '' })
  },
})

// Define model bindings from parent
const doc = defineModel()
const reply = defineModel('reply')
const whapi = defineModel('sms')
const show = defineModel('show')

// Emit events
const emit = defineEmits(['update:message', 'update:messages'])

// Local state
const message = ref('')
const messageInput = ref(null)
const closeButton = ref(null)
const sendButton = ref(null)

// Watch for show to auto-focus input
watch(show, (newValue) => {
  if (newValue) {
    nextTick(() => {
      messageInput.value?.focus()
    })
  }
})

// Watch message changes
watch(message, (newValue) => {
  console.log('Message changed:', newValue)
})

// Resource for sending the Whapi message
const sendMessageResource = createResource({
  url: 'crm.api.sms.send_message',
  makeParams() {
    console.log('Current message value:', message.value)
    if (!doc.value?.data?.name) {
      throw new Error('Document name is required')
    }
    if (!doc.value?.data?.mobile_no) {
      throw new Error('Mobile number is required')
    }
    if (!message.value) {
      throw new Error('Message is required')
    }
    
    const params = {
      reference_doctype: props.contact.doctype,
      reference_name: doc.value.data.name,
      message: message.value,
      recipient: doc.value.data.mobile_no
    }
    console.log('Sending Whapi message with params:', params)
    return params
  },
  onSuccess(data) {
    console.log('Whapi message sent successfully:', data)
    message.value = ''
    closeBox()
    whapi?.reload?.()
  },
  onError(error) {
    console.error('Error sending Whapi message:', error)
  }
})

// Send message trigger
function sendMessage() {
  try {
    console.log('Send message triggered with value:', message.value)
    if (!message.value) {
      return
    }
    sendMessageResource.submit()
  } catch (error) {
    console.error('Error in sendMessage:', error)
  }
}

// Close box function
function closeBox() {
  show.value = false
  message.value = ''
}

// Expose focusable elements for dialog support
defineExpose({
  focusableElements: () => [
    messageInput.value,
    closeButton.value,
    sendButton.value,
  ].filter(Boolean),
})
</script>

<style scoped>
.min-h-[120px] {
  min-height: 120px;
}
</style> 