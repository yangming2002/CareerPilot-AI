<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'

const router = useRouter()
const searchQ = ref('')
const archives = ref<any[]>([])
const loading = ref(false)

async function loadHistory(q = '') {
  loading.value = true
  try {
    const { data } = await client.get('/api/v1/analysis/jd-history', { params: { q } })
    archives.value = data
  } catch {
    archives.value = []
  } finally {
    loading.value = false
  }
}

function search() {
  loadHistory(searchQ.value.trim())
}

onMounted(() => loadHistory())
</script>

<template>
  <div class="history-page">
    <div class="page-header">
      <h1>JD 历史库</h1>
      <p>每次分析过的 JD 自动归档，可以搜索、回顾匹配结果。JD 有效期请自行确认。</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQ"
        placeholder="搜索公司、岗位、技能关键词..."
        @keyup.enter="search"
        clearable
      >
        <template #append>
          <el-button @click="search" :loading="loading">搜索</el-button>
        </template>
      </el-input>
    </div>

    <el-table v-if="archives.length" :data="archives" stripe v-loading="loading" style="width:100%">
      <el-table-column prop="company" label="公司" width="160">
        <template #default="{ row }">
          {{ row.company || '未识别' }}
        </template>
      </el-table-column>
      <el-table-column prop="position" label="岗位" width="180">
        <template #default="{ row }">
          {{ row.position || '未识别' }}
        </template>
      </el-table-column>
      <el-table-column label="匹配分" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.match_score !== null" :type="row.match_score >= 70 ? 'success' : row.match_score >= 40 ? 'warning' : 'danger'" size="small">
            {{ row.match_score }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="技能标签" min-width="200">
        <template #default="{ row }">
          <el-tag v-for="t in (row.tags || '').split(',').filter(Boolean).slice(0, 6)" :key="t" size="small" style="margin:2px">
            {{ t }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="分析时间" width="170">
        <template #default="{ row }">
          {{ row.created_at?.slice(0, 16)?.replace('T', ' ') }}
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-else-if="!loading" description="暂无归档 JD，开始分析第一份岗位吧" />

    <div class="back-link">
      <el-button text @click="router.push('/')">← 返回工作台</el-button>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin-bottom: 8px;
  color: #111827;
  font-size: 24px;
}

.page-header p {
  color: #667085;
  font-size: 14px;
}

.search-bar {
  margin-bottom: 20px;
}

.back-link {
  margin-top: 24px;
}
</style>
