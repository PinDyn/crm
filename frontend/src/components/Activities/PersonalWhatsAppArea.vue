<template>
  <div class="flex flex-col h-full">
    <div ref="messagesContainer" class="flex-1 overflow-y-auto">
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
              <!-- Media Content -->
              <div v-if="message.attach" class="mb-2">
                <!-- Image -->
                <img 
                  v-if="message.isImage" 
                  :src="message.mediaUrl" 
                  :alt="message.message || 'Image'"
                  class="max-w-full rounded-lg cursor-pointer"
                  @click="openMediaViewer(message.mediaUrl, message.content_type)"
                  @error="handleImageError"
                />
                <!-- Video -->
                <video 
                  v-else-if="message.isVideo" 
                  :src="message.mediaUrl" 
                  controls
                  class="max-w-full rounded-lg"
                  preload="metadata"
                >
                  <source :src="message.mediaUrl" :type="message.content_type">
                  Your browser does not support the video tag.
                </video>
                <!-- Audio -->
                <audio 
                  v-else-if="message.isAudio" 
                  :src="message.mediaUrl" 
                  controls
                  class="cursor-pointer"
                />
                <!-- Document/File -->
                <div 
                  v-else 
                  class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg cursor-pointer"
                  @click="downloadFile(message.mediaUrl, message.message)"
                >
                  <FeatherIcon name="file" class="h-6 w-6 text-gray-500" />
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium truncate">{{ message.message || 'Document' }}</div>
                    <div class="text-xs text-gray-500">{{ getFileExtension(message.attach) }}</div>
                  </div>
                  <FeatherIcon name="download" class="h-4 w-4 text-gray-500" />
                </div>
              </div>
              
              <!-- Text Message Content -->
              <div 
                v-if="message.message && message.message.trim()"
                class="text-sm"
                :class="message.type === 'Outgoing' ? 'text-white' : 'text-gray-900'"
                v-html="formatWhapiMessage(message.message)"
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
const messagesContainer = ref(null)
const emit = defineEmits(['reply', 'react', 'delete', 'reload'])

const messages = computed(() => {
  if (!props.messages) return [];
  return props.messages.map(msg => ({
    ...msg,
    // Only format text messages, not media URLs
    message: msg.attach && msg.content_type ? msg.message : formatWhapiMessage(msg.message),
    // Add computed properties for better media handling
    isImage: isImageFile(msg.attach, msg.content_type),
    isVideo: isVideoFile(msg.attach, msg.content_type),
    isAudio: isAudioFile(msg.attach, msg.content_type),
    mediaUrl: getMediaUrl(msg.attach)
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
  if (messagesContainer.value) {
    // Simple and direct scrolling
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Scroll to bottom on mount
onMounted(() => {
  nextTick(() => {
    scrollToBottom()
  })
})

// Also scroll to bottom when messages change
watch(() => props.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true, immediate: true })

// Additional watcher for when the container is ready
watch(() => messagesContainer.value, (container) => {
  if (container) {
    nextTick(() => {
      scrollToBottom()
    })
  }
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

// Media detection functions
function isImageFile(attach, contentType) {
  if (!attach) return false
  
  // Check content type first
  if (contentType && contentType.startsWith('image/')) {
    return true
  }
  
  // Fallback: check file extension
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  const extension = getFileExtension(attach).toLowerCase()
  return imageExtensions.includes(extension)
}

function isVideoFile(attach, contentType) {
  if (!attach) return false
  
  // Check content type first
  if (contentType && contentType.startsWith('video/')) {
    return true
  }
  
  // Fallback: check file extension
  const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
  const extension = getFileExtension(attach).toLowerCase()
  return videoExtensions.includes(extension)
}

function isAudioFile(attach, contentType) {
  if (!attach) return false
  
  // Check content type first
  if (contentType && contentType.startsWith('audio/')) {
    return true
  }
  
  // Fallback: check file extension (handle cases with codecs info)
  const audioExtensions = ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a']
  let extension = getFileExtension(attach).toLowerCase()
  
  // Remove codecs info if present (e.g., "ogg; codecs=opus" -> "ogg")
  if (extension.includes(';')) {
    extension = extension.split(';')[0].trim()
  }
  
  return audioExtensions.includes(extension)
}

function getMediaUrl(attach) {
  if (!attach) return ''
  
  console.log('Processing media URL:', attach)
  
  // Clean the attach string (remove codecs info if present)
  let cleanAttach = attach
  if (cleanAttach.includes('; codecs=')) {
    cleanAttach = cleanAttach.split('; codecs=')[0]
    console.log('Cleaned codecs info:', cleanAttach)
  }
  
  // If it's already a full URL, return as is
  if (cleanAttach.startsWith('http://') || cleanAttach.startsWith('https://')) {
    console.log('Full URL detected:', cleanAttach)
    return cleanAttach
  }
  
  // If it's a file path starting with /files/, convert to proper URL
  if (cleanAttach.startsWith('/files/')) {
    // Get the current domain
    const baseUrl = window.location.origin
    const fullUrl = `${baseUrl}${cleanAttach}`
    console.log('Converted file path to URL:', fullUrl)
    return fullUrl
  }
  
  // If it's a relative path, assume it's relative to the current domain
  if (cleanAttach.startsWith('/')) {
    const baseUrl = window.location.origin
    const fullUrl = `${baseUrl}${cleanAttach}`
    console.log('Converted relative path to URL:', fullUrl)
    return fullUrl
  }
  
  // Otherwise, return as is (might be a data URL or other format)
  console.log('Returning as-is:', cleanAttach)
  return cleanAttach
}

// Media handling functions
function openMediaViewer(url, contentType) {
  if (contentType && contentType.startsWith('image/')) {
    // Open image in new tab for full view
    window.open(url, '_blank')
  }
}

function downloadFile(url, filename) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function getFileExtension(url) {
  if (!url) return ''
  const filename = url.split('/').pop()
  return filename.split('.').pop().toUpperCase()
}

function handleImageError(event) {
  console.log('Image failed to load:', event.target.src)
  // Optionally show a fallback or error message
  event.target.style.display = 'none'
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

/* Media styling */
img {
  max-width: 300px;
  max-height: 300px;
  object-fit: cover;
}

video {
  max-width: 300px;
  max-height: 300px;
}

audio {
  max-width: 300px;
}
</style> 