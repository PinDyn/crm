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
            message.type === 'Outgoing' ? 'bg-blue-50' : 'bg-gray-50',
          ]"
        >
          <div class="flex w-full flex-col gap-1">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="text-sm font-medium text-gray-700">
                  {{ message.type === 'Outgoing' ? 'You' : message.sender }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ formatDate(message.creation) }}
                </div>
              </div>
              <Dropdown :options="getMessageOptions(message)">
                <template #default>
                  <Button variant="ghost" class="h-6 w-6 p-0">
                    <FeatherIcon name="more-vertical" class="h-4 w-4" />
                  </Button>
                </template>
              </Dropdown>
            </div>
            <div class="text-sm text-gray-900">
              {{ message.content }}
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatDate, timeAgo } from '@/utils'
import { Tooltip, createResource, FeatherIcon, Dropdown, Button, TextEditor } from 'frappe-ui'

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
  messages: {
    type: Array,
    default: () => [],
  },
})

const showNewMessage = ref(false)
const newMessage = ref('')

const messagesResource = createResource({
  url: 'crm.api.sms.get_sms_messages',
  params: {
    contact: props.contact.name,
  },
  auto: true,
})

const messages = computed(() => messagesResource.data || [])

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
  url: 'crm.api.sms.send_sms',
  makeParams() {
    return {
      contact: props.contact.name,
      message: newMessage.value,
    }
  },
  onSuccess() {
    newMessage.value = ''
    showNewMessage.value = false
    messagesResource.reload()
  },
})

function sendMessage() {
  if (!newMessage.value.trim()) return
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

const emit = defineEmits(['reply', 'react', 'delete'])
</script> 