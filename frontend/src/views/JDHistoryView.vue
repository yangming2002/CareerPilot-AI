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

function parseTags(tags: string): string[] {
  if (!tags) return []
  return tags.split(/[,，；;]/).map(t => t.trim()).filter(t => t.length > 0)
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
      <p>每次分析过的 JD 自动归档。点击行展开查看完整 JD 描述。JD 有效期请自行确认。</p>
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

    <el-table v-if="archives.length" :data="archives" stripe v-loading="loading" style="width:100%" table-layout="auto">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="jd-expand">
            <div class="jd-meta">
              <span v-if="row.company"><strong>公司：</strong>{{ row.company }}</span>
              <span v-if="row.position"><strong>岗位：</strong>{{ row.position }}</span>
              <span v-if="row.match_score !== null"><strong>匹配分：</strong>{{ row.match_score }}</span>
              <span v-if="row.created_at"><strong>时间：</strong>{{ row.created_at?.slice(0, 16)?.replace('T', ' ') }}</span>
            </div>
            <div class="jd-tags" v-if="row.tags">
              <el-tag v-for="t in parseTags(row.tags)" :key="t" size="small" style="margin:2px">{{ t }}</el-tag>
            </div>
            <div class="jd-full-text">{{ row.jd_text || row.jd_summary || '暂无 JD 描述' }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="company" label="公司" min-width="120" />
      <el-table-column prop="position" label="岗位" min-width="150" />
      <el-table-column label="匹配" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.match_score !== null" :type="row.match_score >= 70 ? 'success' : row.match_score >= 40 ? 'warning' : 'danger'" size="small">
            {{ row.match_score }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="检索来源" width="140">
        <template #default="{ row }">
          <template v-if="row.sources?.length">
            <el-tag v-for="s in row.sources.slice(0,2)" :key="s" size="small" type="info" style="margin:1px">{{ s }}</el-tag>
          </template>
          <span v-else style="color:#9ca3af">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="150">
        <template #default="{ row }">
          {{ row.created_at?.slice(0, 16)?.replace('T', ' ') || '-' }}
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}
.page-header { margin-bottom: 24px; }
.page-header h1 { margin-bottom: 8px; color: #111827; font-size: 24px; }
.page-header p { color: #667085; font-size: 14px; }
.search-bar { margin-bottom: 20px; }
.back-link { margin-top: 24px; }

.jd-expand {
  padding: 16px 20px;
  background: #f9fafb;
  border-radius: 6px;
}
.jd-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #374151;
}
.jd-meta span { display: flex; align-items: center; gap: 4px; }
.jd-tags { margin-bottom: 12px; }
.jd-full-text {
  padding: 14px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.8;
  color: #1f2937;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}
</style>
