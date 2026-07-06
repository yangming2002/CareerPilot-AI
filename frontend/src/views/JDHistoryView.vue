<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api/client'

const router = useRouter()
const searchQ = ref('')
const archives = ref<any[]>([])
const loading = ref(false)
const selection = ref<any[]>([])
const page = ref(1)
const total = ref(0)

async function loadHistory(q = '') {
  loading.value = true
  try {
    const params: any = { page: page.value }
    if (q) params.q = q
    const { data } = await client.get('/api/v1/analysis/jd-history', { params })
    archives.value = data.items || data
    total.value = data.total || archives.value.length
  } catch { archives.value = []; total.value = 0 }
  finally { loading.value = false }
}

function search() { page.value = 1; loadHistory(searchQ.value.trim()) }
function handleSelect(rows: any[]) { selection.value = rows }

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' })
    await client.delete(`/api/v1/analysis/jd-history/${id}`)
    ElMessage.success('已删除')
    loadHistory(searchQ.value.trim())
  } catch { }
}

async function batchDelete() {
  if (!selection.value.length) { ElMessage.warning('请先选择'); return }
  try {
    await ElMessageBox.confirm(`确定删除 ${selection.value.length} 条？`, '批量删除', { type: 'warning' })
    await client.post('/api/v1/analysis/jd-history/batch-delete', selection.value.map((a: any) => a.id))
    ElMessage.success('已删除')
    selection.value = []
    loadHistory(searchQ.value.trim())
  } catch { }
}

function parseTags(tags: string): string[] {
  if (!tags) return []
  return tags.split(/[,，；;]/).map(t => t.trim()).filter(t => t.length > 0)
}

onMounted(() => loadHistory())
</script>

<template>
  <div class="history-page">
    <div class="page-header">
      <h1>岗位描述库</h1>
      <p>每次分析过的岗位描述自动归档。点击行展开查看完整内容。</p>
    </div>

    <div class="search-bar">
      <el-input v-model="searchQ" placeholder="搜索公司、岗位、技能..." @keyup.enter="search" clearable>
        <template #append><el-button @click="search" :loading="loading">搜索</el-button></template>
      </el-input>
      <el-button v-if="selection.length" size="small" type="danger" @click="batchDelete" style="margin-left:8px">删除选中({{ selection.length }})</el-button>
    </div>

    <el-table v-if="archives.length" :data="archives" stripe v-loading="loading" @selection-change="handleSelect" style="width:100%">
      <el-table-column type="selection" width="40" />
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="jd-expand">
            <div class="jd-meta">
              <span v-if="row.company"><strong>公司：</strong>{{ row.company }}</span>
              <span v-if="row.position"><strong>岗位：</strong>{{ row.position }}</span>
              <span v-if="row.match_score"><strong>匹配分：</strong>{{ row.match_score }}</span>
            </div>
            <div class="jd-tags" v-if="row.tags">
              <el-tag v-for="t in parseTags(row.tags)" :key="t" size="small" style="margin:2px">{{ t }}</el-tag>
            </div>
            <div class="jd-full-text">{{ row.jd_text || row.jd_summary || '暂无描述' }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="company" label="公司" min-width="120" />
      <el-table-column prop="position" label="岗位" min-width="150" />
      <el-table-column label="匹配分" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.match_score" size="small" :type="row.match_score>=70?'success':row.match_score>=40?'warning':'danger'">{{ row.match_score }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="150" />
      <el-table-column label="" width="70">
        <template #default="{ row }"><el-button size="small" text type="danger" @click="handleDelete(row.id)">删除</el-button></template>
      </el-table-column>
    </el-table>

    <el-empty v-else-if="!loading" description="暂无归档岗位描述" />
    <div style="margin-top:14px;text-align:center" v-if="total > 50">
      <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="prev,pager,next" @change="loadHistory()" small />
    </div>
  </div>
</template>

<style scoped>
.history-page { max-width: 1200px; margin: 0 auto; padding: 32px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 22px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.page-header p { font-size: 13px; color: #6b7280; }
.search-bar { display: flex; align-items: center; margin-bottom: 20px; }
.jd-expand { padding: 16px 20px; background: #f9fafb; border-radius: 6px; }
.jd-meta { display: flex; gap: 24px; margin-bottom: 10px; font-size: 13px; color: #374151; }
.jd-tags { margin-bottom: 10px; }
.jd-full-text { padding: 14px; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 13px; line-height: 1.8; color: #1f2937; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
</style>
