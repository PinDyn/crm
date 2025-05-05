<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="text-lg font-medium">SMS Messages</div>
      <Button
        v-if="!showNewMessage"
        icon="plus"
        @click="showNewMessage = true"
      >
        New Message
      </Button>
    </div>

    <div v-if="showNewMessage" class="flex flex-col gap-2 p-4 bg-gray-50 rounded-lg">
      <div class="flex items-end gap-2">
        <TextEditor
          v-model="newMessage"
          class="flex-1 min-h-[100px] bg-white rounded-lg border border-gray-200 p-2"
          placeholder="Type your message..."
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="newMessage += '\n'"
        />
        <Button
          icon="send"
          class="!p-2"
          :disabled="!newMessage.trim()"
          @click="sendMessage"
        />
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <div
        v-for="message in messages"
        :key="message.name"
        class="flex flex-col gap-2"
      >
        <div
          :class="[
            'flex items-start gap-2 rounded-lg p-2',
            message.direction === 'Outgoing' ? 'bg-blue-50' : 'bg-gray-50',
          ]"
        >
          <div class="flex w-full flex-col gap-1">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="text-sm font-medium text-gray-700">
                  {{ message.direction === 'Outgoing' ? 'You' : message.from_number }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ timeAgo(message.creation) }}
                </div>
              </div>
              <div class="text-xs text-gray-500">
                {{ message.status }}
              </div>
            </div>
            <div class="text-sm text-gray-900">
              {{ message.message }}
            </div>
            <div v-if="message.reactions?.length" class="flex gap-1">
              <div
                v-for="reaction in message.reactions"
                :key="reaction.name"
                class="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-1 text-xs"
              >
                <span>{{ reaction.emoji }}</span>
                <span class="text-gray-600">{{ reaction.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="messages.length === 0" class="text-center text-gray-500 py-4">
        No messages found
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, toRaw, isProxy, onMounted } from 'vue'
import { formatDate, timeAgo } from '@/utils'
import { Tooltip, createResource, FeatherIcon, Dropdown, Button, TextEditor } from 'frappe-ui'

const props = defineProps({
  contact: {
    type: Object,
    default: () => null,
  },
  messages: {
    type: Array,
    default: () => [],
  },
})

const showNewMessage = ref(false)
const newMessage = ref('')

const messages = computed(() => {
  console.log('SMSArea - Raw messages prop:', props.messages);
  if (!props.messages) {
    console.log('SMSArea - No messages prop');
    return [];
  }
  // Convert to plain array to avoid reactivity issues
  const plainMessages = Array.isArray(props.messages) ? props.messages : [];
  const formattedMessages = plainMessages.map(msg => {
    // Convert to plain object
    const plainMsg = JSON.parse(JSON.stringify(msg));
    return {
      ...plainMsg,
      message: formatSMSMessage(plainMsg.message)
    };
  });
  console.log('SMSArea - Formatted messages:', formattedMessages);
  return formattedMessages;
});

// Add watcher to track message changes
watch(() => props.messages, (newMessages) => {
  console.log('SMSArea - Messages prop changed:', newMessages);
}, { deep: true });

// Add watcher to track contact changes
watch(() => props.contact, (newContact) => {
  console.log('SMSArea - Contact prop changed:', newContact);
}, { deep: true });

function formatSMSMessage(message) {
  // if message contains _text_, make it italic
  message = message.replace(/_(.*?)_/g, '<i>$1</i>')
  // if message contains *text*, make it bold
  message = message.replace(/\*(.*?)\*/g, '<b>$1</b>')
  // if message contains ~text~, make it strikethrough
  message = message.replace(/~(.*?)~/g, '<s>$1</s>')
  // if message contains ```text```, make it monospace
  message = message.replace(/```(.*?)```/g, '<code>$1</code>')
  // if message contains `text`, make it inline code
  message = message.replace(/`(.*?)`/g, '<code>$1</code>')
  // if message contains > text, make it a blockquote
  message = message.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
  // if contain /n, make it a new line
  message = message.replace(/\n/g, '<br>')
  // if contains *<space>text, make it a bullet point
  message = message.replace(/\* (.*?)(?=\s*\*|$)/g, '<li>$1</li>')
  message = message.replace(/- (.*?)(?=\s*-|$)/g, '<li>$1</li>')
  message = message.replace(/(\d+)\. (.*?)(?=\s*(\d+)\.|$)/g, '<li>$2</li>')

  return message
}

function scrollToMessage(name) {
  const element = document.getElementById(name)
  element.scrollIntoView({ behavior: 'smooth' })

  // Highlight the message
  element.classList.add('bg-yellow-100')
  setTimeout(() => {
    element.classList.remove('bg-yellow-100')
  }, 1000)
}

const sendMessageResource = createResource({
  url: 'frappe_sms.api.sms.send_sms',
  makeParams() {
    const params = {
      reference_doctype: props.contact.doctype,
      reference_name: props.contact.name,
      message: newMessage.value,
      recipient: props.contact.mobile_no
    }
    console.log('SMSArea - Sending SMS with params:', params)
    return params
  },
  onSuccess(data) {
    console.log('Message sent successfully:', data)
    newMessage.value = ''
    showNewMessage.value = false
    // Emit an event to reload messages
    emit('reload')
  },
  onError(error) {
    console.error('Error sending message:', error)
  }
})

function sendMessage() {
  if (!newMessage.value.trim()) return
  console.log('Sending message:', newMessage.value)
  sendMessageResource.submit()
}

const getMessageOptions = (message) => {
  return [
    {
      label: 'Reply',
      icon: 'corner-up-left',
      onClick: () => emit('reply', message),
    },
    {
      label: 'React',
      icon: 'thumbs-up',
      onClick: () => emit('react', message),
    },
    {
      label: 'Delete',
      icon: 'trash-2',
      onClick: () => emit('delete', message),
    },
  ]
}

const emit = defineEmits(['reply', 'react', 'delete', 'reload'])
</script> 