<template>
  <div class="flex flex-col gap-4 h-full">
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
            :class="message.type === 'Outgoing' ? 'text-right' : 'text-left'"
          >
            {{ message.type === 'Outgoing' ? 'You' : message.from }} • {{ timeAgo(message.creation) }}
          </div>
          
          <!-- Message Bubble -->
          <div
            :class="[
              'flex items-start gap-2 rounded-lg p-3 max-w-[80%] shadow-sm',
              message.type === 'Outgoing' 
                ? 'ml-auto bg-green-500 text-white' 
                : 'mr-auto bg-gray-100 text-gray-900',
            ]"
          >
            <div class="flex w-full flex-col gap-1">
              <!-- Message Content -->
              <div 
                class="text-sm"
                :class="message.type === 'Outgoing' ? 'text-white' : 'text-gray-900'"
                v-html="message.message"
              />
              
              <!-- Message Status -->
              <div 
                class="flex items-center gap-1 text-xs"
                :class="message.type === 'Outgoing' ? 'text-green-100' : 'text-gray-500'"
              >
                <span v-if="message.type === 'Outgoing'">
                  {{ message.status || 'Sent' }}
                </span>
              </div>
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

const newMessage = ref('')
const emit = defineEmits(['reply', 'react', 'delete', 'reload'])



const messages = computed(() => {
  if (!props.messages) return [];
  return props.messages.map(msg => ({
    ...msg,
    message: formatWhapiMessage(msg.message)
  }));
});

// Add auto-scroll to bottom when new messages arrive
watch(() => props.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// Function to scroll to bottom
function scrollToBottom() {
  const container = document.querySelector('.overflow-y-auto')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

// Scroll to bottom on mount
onMounted(() => {
  nextTick(() => {
    scrollToBottom()
  })
})

function formatWhapiMessage(message) {
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
  url: 'crm.api.sms.send_message',
  makeParams() {
    const params = {
      reference_doctype: props.contact.doctype,
      reference_name: props.contact.name,
      message: newMessage.value,
      recipient: props.contact.mobile_no
    }
    console.log('PersonalWhatsAppArea - Sending Whapi message with params:', params)
    return params
  },
  onSuccess(data) {
    console.log('Message sent successfully:', data)
    newMessage.value = ''
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