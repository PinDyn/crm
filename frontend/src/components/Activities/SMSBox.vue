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

const props = defineProps({
  contact: {
    type: Object,
    required: true,
    default: () => ({ doctype: 'CRM Lead', name: '', mobile_no: '' })
  },
})

const emit = defineEmits(['update:show', 'update:message', 'update:messages'])

const show = ref(false)
const message = ref('')
const messages = ref(null)
const messageInput = ref(null)
const closeButton = ref(null)
const sendButton = ref(null)

watch(show, (newValue) => {
  if (newValue) {
    // Focus the text editor when the dialog opens
    nextTick(() => {
      messageInput.value?.focus()
    })
  }
})

const sendMessageResource = createResource({
  url: 'frappe_sms.api.sms.send_sms',
  makeParams() {
    if (!props.contact?.doctype || !props.contact?.name) {
      console.error('Contact prop is missing required properties')
      return null
    }
    return {
      reference_doctype: props.contact.doctype,
      reference_name: props.contact.name,
      message: message.value,
      recipient: props.contact.mobile_no,
    }
  },
  onSuccess() {
    message.value = ''
    show.value = false
    messages.value?.reload()
  },
})

function sendMessage() {
  if (!message.value) return
  sendMessageResource.submit()
}

// Expose focusable elements for the dialog
defineExpose({
  focusableElements: () => [
    messageInput.value,
    closeButton.value,
    sendButton.value,
  ].filter(Boolean),
})
</script> 