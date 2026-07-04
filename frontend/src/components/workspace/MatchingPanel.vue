<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
</script>

<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">
        <span>JD 匹配分析</span>
        <el-tag size="small">用户主动记录</el-tag>
      </div>
    </template>

    <el-input
      v-model="store.jdText"
      type="textarea"
      :rows="14"
      resize="none"
      placeholder="请粘贴你真正想投递的公司 JD。系统围绕该 JD 输出匹配报告，不默认联网搜索或编造岗位信息。"
    />

    <el-button
      type="primary"
      size="large"
      :loading="store.loading"
      style="margin-top: 16px; width: 100%"
      @click="store.analyze()"
    >
      生成匹配分析
    </el-button>

    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
      style="margin-top: 12px"
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
