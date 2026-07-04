<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>简历内容</span>
        <el-tag size="small" type="warning">敏感数据</el-tag>
      </div>
    </template>

    <el-input
      v-model="store.resumeText"
      type="textarea"
      :rows="14"
      resize="none"
      placeholder="请粘贴简历文本。后端接入后，简历默认只用于本次分析，不写入公共知识库。"
    />
  </el-card>
</template>

<style scoped>
.panel-card {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
