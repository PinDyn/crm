<template>
  <div class="flex flex-col gap-4 h-full">
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

    <div class="flex-1 overflow-y-auto">
      <div class="flex flex-col gap-4 p-4">
        <div
          v-for="message in messages"
          :key="message.name"
          :id="message.name"
          class="flex flex-col gap-1"
        >
          <!-- Message Header -->
          <div 
            class="text-xs text-gray-500 px-2"
            :class="message.direction === 'Outgoing' ? 'text-right' : 'text-left'"
          >
            {{ message.direction === 'Outgoing' ? 'You' : message.from_number }} • {{ timeAgo(message.creation) }}
          </div>
          
          <!-- Message Bubble -->
          <div
            :class="[
              'flex items-start gap-2 rounded-lg p-3 max-w-[80%] shadow-sm',
              message.direction === 'Outgoing' 
                ? 'ml-auto bg-blue-500 text-white' 
                : 'mr-auto bg-gray-100 text-gray-900',
            ]"
          >
            <div class="flex w-full flex-col gap-1">
              <!-- Message Content -->
              <div 
                class="text-sm"
                :class="message.direction === 'Outgoing' ? 'text-white' : 'text-gray-900'"
                v-html="message.message"
              />
              
              <!-- Message Status -->
              <div 
                class="flex items-center gap-1 text-xs"
                :class="message.direction === 'Outgoing' ? 'text-blue-100' : 'text-gray-500'"
              >
                <span v-if="message.direction === 'Outgoing'">
                  {{ message.status }}
                </span>
              </div>
            </div>
          </div>

          <!-- Reactions -->
          <div 
            v-if="message.reactions?.length" 
            class="flex gap-1 px-2"
            :class="message.direction === 'Outgoing' ? 'justify-end' : 'justify-start'"
          >
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

        <!-- Empty State -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500 py-8">
          <div class="text-lg mb-2">No messages yet</div>
          <div class="text-sm">Start a conversation by sending a message</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, toRaw, isProxy, onMounted, onUnmounted, nextTick } from 'vue'
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
const emit = defineEmits(['reply', 'react', 'delete', 'reload'])

// Add polling for new messages
let pollInterval = null

onMounted(() => {
  // Start polling every 5 seconds
  pollInterval = setInterval(() => {
    emit('reload')
  }, 5000)
})

onUnmounted(() => {
  // Clean up polling when component is destroyed
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})

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

// Add auto-scroll to bottom when new messages arrive
watch(() => props.messages, () => {
  nextTick(() => {
    const container = document.querySelector('.overflow-y-auto')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}, { deep: true })

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
  sendMessageResource.submit()
  // Emit reload event after sending message
  emit('reload')
  // Clear the message input
  newMessage.value = ''
  showNewMessage.value = false
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
</script>

<style scoped>
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}

.max-w-[80%] {
  max-width: 80%;
}
</style> 