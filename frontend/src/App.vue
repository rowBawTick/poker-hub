<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-poker-green text-white shadow-md">
      <div class="container mx-auto px-4 py-3 flex justify-between items-center">
        <router-link to="/" class="text-xl font-bold">Poker Hud</router-link>
        <nav>
          <router-link to="/" class="px-3 py-2 hover:text-gray-200">Home</router-link>
        </nav>
      </div>
    </header>

    <main class="container mx-auto px-4 py-6">
      <router-view />
    </main>

    <footer class="bg-gray-800 text-white py-4">
      <div class="container mx-auto px-4 text-center text-sm">
        <p>Poker Hud - Your Poker Stats Dashboard</p>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
};
</script>
