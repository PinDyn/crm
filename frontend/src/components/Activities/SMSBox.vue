<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="text-lg font-medium">New SMS</div>
      <Button
        ref="closeButton"
        icon="x"
        variant="ghost"
        class="h-6 w-6 p-0"
        @click="show = false"
      />
    </div>

    <div class="flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <div class="flex-1">
          <Input
            v-model="message"
            type="textarea"
            :placeholder="__('Type your message here...')"
            @keydown.enter.prevent="sendMessage"
          />
        </div>
      </div>
    </div>
    <div class="flex justify-end gap-2">
      <Button @click="show = false">{{ __('Cancel') }}</Button>
      <Button
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
import { createResource, Button, Input } from 'frappe-ui'

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
const sms = defineModel('sms')

// Emit events (if needed in other logic)
const emit = defineEmits(['update:show', 'update:message', 'update:messages'])

// Local state
const show = ref(false)
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

// Resource for sending the SMS
const sendMessageResource = createResource({
  url: 'frappe_sms.api.sms.send_sms',
  makeParams() {
    const { doctype } = props.contact || {};
    let missingProps = [];

    // Check for missing properties and log the names
    if (!doctype) missingProps.push('doctype');
    if (!doc.value.data.name) missingProps.push('name');
    if (!doc.value.data.mobile_no) missingProps.push('mobile_no');

    if (missingProps.length) {
      console.error(`Missing required properties: ${missingProps.join(', ')}`);
      return null;
    }

    // Log only essential information
    const params = {
      reference_doctype: doctype,
      reference_name: doc.value.data.name,
      message: message.value,
      recipient: doc.value.data.mobile_no
    };
    console.log('Sending SMS to:', doc.value.data.mobile_no);

    return params;
  },
  onSuccess() {
    message.value = ''
    show.value = false
    sms?.reload?.()
  },
})

// Send message trigger
function sendMessage() {
  if (!message.value) return
  sendMessageResource.submit()
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
 