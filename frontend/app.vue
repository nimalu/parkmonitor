<template>
  <div class="min-h-screen bg-background">
    <div class="container mx-auto py-8 px-4">
      <header class="mb-8">
        <h1 class="text-4xl font-bold mb-2">ParkMonitor Dashboard</h1>
        <p class="text-muted-foreground">Real-time parking data and AI-powered forecasts</p>
      </header>

      <!-- Loading State -->
      <div v-if="pending" class="flex items-center justify-center py-12">
        <div class="text-center">
          <Icon name="lucide:loader-2" class="w-8 h-8 animate-spin mx-auto mb-2" />
          <p class="text-muted-foreground">Loading parking data...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="py-12">
        <Card class="border-destructive">
          <CardHeader>
            <CardTitle class="text-destructive flex items-center gap-2">
              <Icon name="lucide:alert-circle" class="w-5 h-5" />
              Error Loading Data
            </CardTitle>
            <CardDescription>{{ error.message }}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button @click="refresh" variant="outline">
              <Icon name="lucide:refresh-cw" class="w-4 h-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Dashboard Content -->
      <div v-else-if="currentStatuses && forecasts">
        <!-- Summary Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader class="pb-2">
              <CardDescription>Total Parking Lots</CardDescription>
              <CardTitle class="text-3xl">{{ currentStatuses.length }}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader class="pb-2">
              <CardDescription>Total Spaces</CardDescription>
              <CardTitle class="text-3xl">{{ totalSpaces }}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader class="pb-2">
              <CardDescription>Available Now</CardDescription>
              <CardTitle class="text-3xl text-green-600 dark:text-green-400">{{ totalFree }}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader class="pb-2">
              <CardDescription>Avg. Occupancy</CardDescription>
              <CardTitle class="text-3xl">{{ averageOccupancy.toFixed(1) }}%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <!-- Parking Lots Grid -->
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-semibold">Parking Lots</h2>
          <Button @click="refresh" variant="outline" size="sm">
            <Icon name="lucide:refresh-cw" :class="['w-4 h-4 mr-2', refreshing && 'animate-spin']" />
            Refresh
          </Button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ParkingLotCard
            v-for="status in currentStatuses"
            :key="status.lot_id"
            :current="status"
            :forecast="forecastMap.get(status.lot_id)"
          />
        </div>

        <!-- Last Updated -->
        <div class="mt-8 text-center text-sm text-muted-foreground">
          Last updated: {{ lastUpdated }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CurrentStatus, Forecast } from '~/types/api'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const refreshing = ref(false)
const lastUpdated = ref(new Date().toLocaleTimeString())

// Fetch current status
const { data: currentStatuses, error, pending, refresh: refreshData } = await useFetch<CurrentStatus[]>(
  `${apiBase}/current`,
  {
    server: false,
  }
)

// Fetch forecasts
const { data: forecasts, refresh: refreshForecasts } = await useFetch<Forecast[]>(
  `${apiBase}/forecast`,
  {
    server: false,
  }
)

// Create a map for easy forecast lookup
const forecastMap = computed(() => {
  const map = new Map<string, Forecast>()
  if (forecasts.value) {
    forecasts.value.forEach(forecast => {
      map.set(forecast.lot_id, forecast)
    })
  }
  return map
})

// Computed stats
const totalSpaces = computed(() => {
  if (!currentStatuses.value) return 0
  return currentStatuses.value.reduce((sum, status) => sum + status.total, 0)
})

const totalFree = computed(() => {
  if (!currentStatuses.value) return 0
  return currentStatuses.value.reduce((sum, status) => sum + status.free, 0)
})

const averageOccupancy = computed(() => {
  if (!currentStatuses.value || currentStatuses.value.length === 0) return 0
  const sum = currentStatuses.value.reduce((sum, status) => sum + status.occupancy_rate, 0)
  return sum / currentStatuses.value.length
})

// Refresh function
const refresh = async () => {
  refreshing.value = true
  await Promise.all([refreshData(), refreshForecasts()])
  lastUpdated.value = new Date().toLocaleTimeString()
  refreshing.value = false
}

// Auto-refresh every 30 seconds
if (import.meta.client) {
  const interval = setInterval(refresh, 30000)
  onUnmounted(() => clearInterval(interval))
}

useHead({
  title: 'ParkMonitor Dashboard',
  meta: [
    { name: 'description', content: 'Real-time parking data and AI-powered forecasts' }
  ]
})
</script>
