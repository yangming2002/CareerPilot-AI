<script setup lang="ts">
defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="module-card">
    <div class="section-title">
      <h2>工作台模块</h2>
      <span>Agent 自动解析 · 匹配 · 校验 · 改写，记忆系统持续沉淀。</span>
    </div>

    <el-radio-group
      :model-value="modelValue"
      @change="(v: string) => emit('update:modelValue', v)"
    >
      <el-radio-button label="matching">JD 匹配</el-radio-button>
      <el-radio-button label="tracker">投递 Tracker</el-radio-button>
      <el-radio-button label="interview">面试复盘</el-radio-button>
      <el-radio-button label="written">笔试复盘</el-radio-button>
      <el-radio-button label="profile">能力画像</el-radio-button>
    </el-radio-group>
  </div>
</template>

<style scoped>
.module-card {
  margin-bottom: 18px;
  padding: 18px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
}

.section-title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.section-title h2 {
  margin-bottom: 0;
  font-size: 18px;
}

.section-title span {
  color: #667085;
  font-size: 14px;
}
</style>
