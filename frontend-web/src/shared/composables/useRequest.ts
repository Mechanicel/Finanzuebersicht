import { ref } from 'vue'

export function useRequest<T>() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const data = ref<T | null>(null)

  async function run(request: () => Promise<T>) {
    loading.value = true
    error.value = null
    try {
      data.value = await request()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  return { loading, error, data, run }
}
