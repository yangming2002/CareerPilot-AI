<script setup lang="ts">
defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <div class="tabs">
    <button v-for="m in modules" :key="m.key"
      :class="['tab', { active: modelValue === m.key }]"
      @click="emit('update:modelValue', m.key)"
    >{{ m.label }}</button>
  </div>
</template>

<script lang="ts">
const modules = [
  { key: 'matching', label: 'JD 匹配' },
  { key: 'tracker', label: '投递' },
  { key: 'interview', label: '面试复盘' },
  { key: 'written', label: '笔试复盘' },
  { key: 'profile', label: '能力画像' },
]
</script>

<style scoped>
.tabs {
  display: flex; gap: 4px;
  background: #f3f4f6; border-radius: 10px; padding: 3px;
}

.tab {
  padding: 7px 16px; border: none; border-radius: 8px;
  background: transparent; color: #6b7280;
  font-size: 13px; font-weight: 500; cursor: pointer;
  transition: all .15s;
}

.tab:hover { color: #374151; }
.tab.active { background: #fff; color: #111827; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
</style>
