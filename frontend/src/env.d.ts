/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_PUBLISHABLE_KEY: string
  // เพิ่มตัวแปรตัวอื่นๆ ที่คุณมีตรงนี้...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
