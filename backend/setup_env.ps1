# # ============================================
# # 🧠 Turnike tizimi uchun Docker muhiti tayyorlash (Windows 11)
# # ============================================
#
# Write-Host "🚀 Turnike loyihasi uchun muhit tayyorlanmoqda..." -ForegroundColor Cyan
#
# # ---- 1. Asosiy kataloglar
# $folders = @(
#     "db\init",
#     "pgbouncer",
#     "pgbackups"
# )
#
# foreach ($folder in $folders) {
#     if (-Not (Test-Path $folder)) {
#         New-Item -ItemType Directory -Force -Path $folder | Out-Null
#         Write-Host "📁 Yaraldi: $folder"
#     } else {
#         Write-Host "✅ Mavjud: $folder"
#     }
# }
#
# # ---- 2. .env fayl yaratish
# $envFile = ".env"
# if (-Not (Test-Path $envFile)) {
#     @"
# POSTGRES_DB=turnikedb
# POSTGRES_USER=turnikeuser
# POSTGRES_PASSWORD=StrongSecurePass123!
# TZ=Asia/Tashkent
# PGTZ=Asia/Tashkent
# "@ | Set-Content -Path $envFile -Encoding UTF8
#     Write-Host "✅ .env fayl yaratildi"
# } else {
#     Write-Host "⚠️ .env fayl allaqachon mavjud — o‘tkazib yuborildi"
# }
#
# # ---- 3. Pgbouncer konfiguratsiyasi
# $pgbouncerIni = "pgbouncer\pgbouncer.ini"
# if (-Not (Test-Path $pgbouncerIni)) {
#     @"
# [databases]
# turnikedb = host=db port=5432 user=\${POSTGRES_USER} password=\${POSTGRES_PASSWORD} dbname=\${POSTGRES_DB}
#
# [pgbouncer]
# listen_addr = 0.0.0.0
# listen_port = 6432
# auth_type = md5
# auth_file = /bitnami/pgbouncer/userlist.txt
# pool_mode = transaction
# max_client_conn = 2000
# default_pool_size = 100
# min_pool_size = 20
# reserve_pool_size = 50
# reserve_pool_timeout = 5
# ignore_startup_parameters = extra_float_digits
# log_connections = 1
# log_disconnections = 1
# "@ | Set-Content -Path $pgbouncerIni -Encoding UTF8
#     Write-Host "✅ pgbouncer.ini fayli yaratildi"
# } else {
#     Write-Host "⚠️ pgbouncer.ini mavjud — o‘tkazib yuborildi"
# }
#
# # ---- 4. Pgbouncer userlist fayli
# $userlist = "pgbouncer\userlist.txt"
# if (-Not (Test-Path $userlist)) {
#     @"
# "turnikeuser" "StrongSecurePass123!"
# "@ | Set-Content -Path $userlist -Encoding UTF8
#     Write-Host "✅ userlist.txt fayli yaratildi"
# } else {
#     Write-Host "⚠️ userlist.txt mavjud — o‘tkazib yuborildi"
# }
#
# # ---- 5. Init SQL uchun shablon
# $initSql = "db\init\README.txt"
# if (-Not (Test-Path $initSql)) {
#     @"
# 📘 Bu papka kelajakda PostgreSQL uchun boshlang'ich init fayllar (SQL) uchun mo‘ljallangan.
# Masalan:
#   01_init_db.sql
#   02_extensions.sql
#   03_roles.sql
#
# Hozircha bu papka bo‘sh holatda ishlaydi.
# "@ | Set-Content -Path $initSql -Encoding UTF8
#     Write-Host "✅ db/init/README.txt fayli yaratildi"
# } else {
#     Write-Host "⚠️ db/init/README.txt mavjud — o‘tkazib yuborildi"
# }
#
# Write-Host ""
# Write-Host "✅ Muhit tayyor! Endi Docker konteynerlarni ishga tushirish uchun:" -ForegroundColor Green
# Write-Host "👉 docker compose up -d" -ForegroundColor Yellow
# Write-Host ""
# Write-Host "🧩 Ishga tushgandan so‘ng baza porti: localhost:5436 (user: turnikeuser, pass: StrongSecurePass123!)"
# Write-Host ""
