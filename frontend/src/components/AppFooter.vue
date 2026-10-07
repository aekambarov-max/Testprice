<template>
  <footer class="app-footer">
    <div class="container inner">
      <div class="brand">
        <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="7" fill="#fff"/><text x="16" y="22" font-size="16" font-weight="700" fill="var(--price-blue)" text-anchor="middle" font-family="Arial">P</text></svg>
        <b>Price</b>
      </div>
      <nav class="links">
        <a href="#" @click.prevent>{{ $t('footer.info') }}</a>
        <a href="#" @click.prevent>{{ $t('footer.contacts') }}</a>
        <a href="#" @click.prevent>{{ $t('footer.feedback') }}</a>
      </nav>
      <span class="copy">© {{ year }} {{ $t('footer.copy') }}</span>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>

<style scoped>
.app-footer { background: var(--price-blue-dark); color: #dbe7f7; padding: 26px 0; margin-top: 24px; }
.inner { display: flex; align-items: center; gap: 32px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 10px; font-size: 18px; color: #fff; }
.links { display: flex; gap: 24px; }
.links a { color: #dbe7f7; }
.copy { margin-left: auto; font-size: 12px; opacity: 0.8; }
</style>
