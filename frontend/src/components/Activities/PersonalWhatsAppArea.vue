<template>
  <div class="flex flex-col h-full">
    <div ref="messagesContainer" class="flex-1">
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
                <div 
                  v-else-if="message.isAudio" 
                  class="audio-player"
                >
                  <div class="audio-player-content">
                    <div class="audio-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                      </svg>
                    </div>
                    <div class="audio-info">
                      <div class="audio-title">Audio Message</div>
                      <div class="audio-duration">0:00 / 0:00</div>
                    </div>
                    <div class="audio-controls">
                      <audio 
                        :src="message.mediaUrl" 
                        style="display: none;"
                        @loadedmetadata="handleAudioLoaded"
                        @error="handleAudioError"
                        preload="metadata"
                        crossorigin="anonymous"
                      />
                      <button 
                        class="play-pause-btn" 
                        :data-audio-src="message.mediaUrl"
                        @click="toggleAudio($event, message.mediaUrl)"
                      >
                        <svg class="play-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M8 5v14l11-7z"/>
                        </svg>
                        <svg class="pause-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div class="audio-progress">
                    <div class="progress-bar" @click="seekAudio($event, message.mediaUrl)">
                      <div class="progress-fill"></div>
                    </div>
                  </div>
                  <!-- Fallback for failed audio -->
                  <div v-if="message.audioError" class="audio-error">
                    <div class="text-sm text-red-500 mt-2">
                      Audio file not available
                    </div>
                  </div>
                </div>
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

// Simplified scrolling logic - only one watcher
watch(() => props.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// Function to scroll to bottom
function scrollToBottom() {
  // Find the parent FadedScrollableDiv (the one with maskheight attribute)
  const parentScrollable = messagesContainer.value?.closest('[maskheight]')
  if (parentScrollable) {
    parentScrollable.scrollTop = parentScrollable.scrollHeight
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
  message = message.replace(/~(.*?)~/g, '$1')
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
  
  // For audio files, preserve the codec information
  const isAudioFile = isAudioFileFromUrl(attach)
  
  // Clean the attach string (remove codecs info if present) - but preserve for audio
  let cleanAttach = attach
  if (!isAudioFile && cleanAttach.includes('; codecs=')) {
    cleanAttach = cleanAttach.split('; codecs=')[0]
  }
  
  // If it's already a full URL, return as is
  if (cleanAttach.startsWith('http://') || cleanAttach.startsWith('https://')) {
    return cleanAttach
  }
  
  // If it's a file path starting with /files/, convert to proper URL
  if (cleanAttach.startsWith('/files/')) {
    // Get the current domain
    const baseUrl = window.location.origin
    const fullUrl = `${baseUrl}${cleanAttach}`
    return fullUrl
  }
  
  // If it's a relative path, assume it's relative to the current domain
  if (cleanAttach.startsWith('/')) {
    const baseUrl = window.location.origin
    const fullUrl = `${baseUrl}${cleanAttach}`
    return fullUrl
  }
  
  // Otherwise, return as is (might be a data URL or other format)
  return cleanAttach
}

// Helper function to detect audio files from URL
function isAudioFileFromUrl(url) {
  if (!url) return false
  
  // Check file extension
  const audioExtensions = ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a', 'oga', 'opus']
  const extension = getFileExtension(url).toLowerCase()
  
  // Remove codecs info if present for extension check
  let cleanExtension = extension
  if (cleanExtension.includes(';')) {
    cleanExtension = cleanExtension.split(';')[0].trim()
  }
  
  return audioExtensions.includes(cleanExtension)
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

function handleAudioLoaded(event) {
  console.log('Audio loaded successfully:', event.target.src)
  console.log('Audio duration:', event.target.duration)
}

function handleAudioError(event) {
  console.error('Audio failed to load:', event.target.src)
  console.error('Audio error details:', {
    error: event.target.error,
    networkState: event.target.networkState,
    readyState: event.target.readyState
  })
  
  // Set audioError flag on the message
  const audioPlayer = event.target.closest('.audio-player')
  if (audioPlayer) {
    const messageElement = audioPlayer.closest('[id]')
    if (messageElement) {
      const messageId = messageElement.id
      // Find the message in the messages array and set audioError flag
      const message = props.messages.find(msg => msg.name === messageId)
      if (message) {
        message.audioError = true
      }
    }
  }
}

// Audio player functions
function toggleAudio(event, audioSrc) {
  const btn = event.currentTarget
  const audioPlayer = btn.closest('.audio-player')
  const audio = audioPlayer.querySelector('audio')
  const progressFill = audioPlayer.querySelector('.progress-fill')
  const duration = audioPlayer.querySelector('.audio-duration')
  const playIcon = btn.querySelector('.play-icon')
  const pauseIcon = btn.querySelector('.pause-icon')
  
  // Ensure audio source is set
  if (audio.src !== audioSrc) {
    audio.src = audioSrc
  }
  
  if (audio.paused) {
    // Play audio
    audio.play().catch(error => {
      console.error('Error playing audio:', error)
      // Reset button state on error
      btn.classList.remove('playing')
      playIcon.style.display = 'block'
      pauseIcon.style.display = 'none'
    })
    
    btn.classList.add('playing')
    playIcon.style.display = 'none'
    pauseIcon.style.display = 'block'
    
    // Update duration display
    audio.addEventListener('loadedmetadata', function() {
      const audioDuration = audio.duration
      const formattedDuration = formatTime(audioDuration)
      duration.textContent = `0:00 / ${formattedDuration}`
    }, { once: true })
    
    // Update progress
    audio.addEventListener('timeupdate', function() {
      const currentTime = audio.currentTime
      const audioDuration = audio.duration
      const progress = (currentTime / audioDuration) * 100
      progressFill.style.width = `${progress}%`
      
      const formattedCurrent = formatTime(currentTime)
      const formattedDuration = formatTime(audioDuration)
      duration.textContent = `${formattedCurrent} / ${formattedDuration}`
    })
    
    // Handle audio end
    audio.addEventListener('ended', function() {
      btn.classList.remove('playing')
      progressFill.style.width = '0%'
      playIcon.style.display = 'block'
      pauseIcon.style.display = 'none'
      duration.textContent = `0:00 / ${formatTime(audio.duration)}`
    }, { once: true })
    
  } else {
    // Pause audio
    audio.pause()
    btn.classList.remove('playing')
    playIcon.style.display = 'block'
    pauseIcon.style.display = 'none'
  }
}

function seekAudio(event, audioSrc) {
  const progressBar = event.currentTarget
  const audioPlayer = progressBar.closest('.audio-player')
  const audio = audioPlayer.querySelector('audio')
  const progressFill = audioPlayer.querySelector('.progress-fill')
  
  if (audio.duration) {
    const rect = progressBar.getBoundingClientRect()
    const clickX = event.clientX - rect.left
    const progressBarWidth = rect.width
    const percentage = (clickX / progressBarWidth) * 100
    const newTime = (percentage / 100) * audio.duration
    
    audio.currentTime = newTime
    progressFill.style.width = `${percentage}%`
  }
}

function formatTime(seconds) {
  if (isNaN(seconds)) return '0:00'
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
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

/* Custom Audio Player Styling */
.audio-player {
  display: flex;
  flex-direction: column;
  margin: 6px 0;
  padding: 12px 16px;
  border-radius: 18px;
  background: var(--message-received-bg, #f3f4f6);
  border: 1px solid var(--border-color, #e5e7eb);
  box-shadow: 0 1px 3px var(--shadow-color, rgba(0, 0, 0, 0.1));
  max-width: 280px;
  min-width: 200px;
  position: relative;
  overflow: hidden;
}

.audio-player-content {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.audio-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary-color, #3b82f6);
  color: white;
  flex-shrink: 0;
}

.audio-info {
  flex: 1;
  min-width: 0;
}

.audio-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color, #374151);
  margin-bottom: 2px;
}

.audio-duration {
  font-size: 12px;
  color: var(--text-secondary, #6b7280);
}

.audio-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.play-pause-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.play-pause-btn:hover {
  background: var(--primary-hover, #2563eb);
  transform: scale(1.05);
}

.play-pause-btn.playing {
  background: var(--primary-active, #1d4ed8);
}

.audio-progress {
  width: 100%;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--progress-bg, #e5e7eb);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.progress-bar:hover {
  background: var(--progress-hover, #d1d5db);
}

.progress-fill {
  height: 100%;
  background: var(--primary-color, #3b82f6);
  border-radius: 2px;
  width: 0%;
  transition: width 0.1s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background: var(--primary-color, #3b82f6);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.progress-bar:hover .progress-fill::after {
  opacity: 1;
}

/* Legacy audio element styling (hidden) */
audio {
  display: none !important;
}
</style> 