# Database Architecture

## Overview

یک سیستم کامل مدیریت کاربران، پرداخت‌ها، و سرویس‌ها

## Tables

### 1. **users** - اطلاعات کاربران

```sql
- id (PK): شناسه منحصر به فرد
- telegram_id (UNIQUE): شناسه کاربر تلگرام
- username: نام کاربری تلگرام
- first_name, last_name: نام و نام خانوادگی
- is_admin: آیا ادمین است؟ (فقط برای غیر ادمین اکنون)
- is_active: فعال/غیرفعال
- referrer_id (FK): کاربری که این کاربر را دعوت کرده
- balance: موجودی کیف پول
- created_at, updated_at: زمان ایجاد و آپدیت
```

### 2. **referral_links** - لینک‌های دعوت

```sql
- id (PK)
- user_id (FK, UNIQUE): کاربر
- invite_code (UNIQUE): کد دعوت یکتا
- click_count: تعداد کلیک
- referral_count: تعداد دعوت موفق
- created_at, updated_at
```

### 3. **referral_rewards** - پاداش‌های دعوت

```sql
- id (PK)
- referrer_user_id (FK): کاربری که دعوت کرده
- referred_user_id (FK): کاربری که دعوت شده
- reward_amount: مقدار پاداش
- is_claimed: آیا دریافت شده؟
- created_at, claimed_at
```

### 4. **clients** - کلاینت‌های VPN/اتصال

```sql
- id (PK)
- user_id (FK): صاحب کلاینت
- email: ایمیل کلاینت
- uuid: شناسه یونیورسال
- inbound_id: شناسه اینباند پنل
- status: active/disabled/expired
- total_gb: کل دیتا
- used_gb: دیتای استفاده شده
- expiry_date: تاریخ انقضا
- created_at, updated_at
```

### 5. **payments** - تراکنش‌های پرداخت

```sql
- id (PK)
- user_id (FK): پرکننده
- amount: مقدار
- status: pending/verified/rejected/refunded
- payment_type: balance_increase / service_purchase
- related_client_id (FK): کلاینت مرتبط (اگر خرید سرویس باشد)
- receipt_image_url: آدرس عکس فیش
- bank_card_number: شماره کارت
- bank_name: نام بانک
- description: توضیحات
- admin_note: یادداشت پشتیبان
- created_at, verified_at, verified_by_admin_id
```

### 6. **payment_methods** - روش‌های پرداخت ادمین

```sql
- id (PK)
- admin_id (FK): ادمینی که تنظیم کرده
- card_number: شماره کارت
- card_holder_name: نام صاحب کارت
- bank_name: نام بانک
- amount_per_payment: مبلغ برای هر پرداخت
- is_active: فعال/غیرفعال
- created_at, updated_at
```

### 7. **service_packages** - بسته‌های سرویس

```sql
- id (PK)
- name: نام بسته
- description: توضیح
- gb_amount: مقدار دیتا بر حسب بایت
- price: قیمت
- duration_days: مدت روز
- is_active: فعال/غیرفعال
- created_at, updated_at
```

### 8. **user_service_subscriptions** - اشتراک کاربران

```sql
- id (PK)
- user_id (FK)
- service_package_id (FK)
- status: active/expired/cancelled
- expiry_date: تاریخ انقضا
- created_at
```

### 9. **support_tickets** - تیکت‌های پشتیبانی

```sql
- id (PK)
- user_id (FK)
- subject: موضوع
- description: متن
- status: open/in_progress/resolved/closed
- assigned_admin_id (FK): ادمین مسئول
- created_at, updated_at
```

### 10. **admin_logs** - گزارش اقدامات ادمین

```sql
- id (PK)
- admin_id (FK): کدام ادمین
- action: نوع اقدام
- target_user_id (FK): کاربر مورد عمل
- description: توضیح
- changes: تغییرات (JSON)
- created_at
```

## Relationships

```
users (1) ──→ (1) referral_links
         ──→ (N) clients
         ──→ (N) payments
         ──→ (N) user_service_subscriptions
         ──→ (N) support_tickets
         ──→ (N) admin_logs (as admin)
         ──→ (1) users (referrer_id)

clients ──→ payments

service_packages ──→ user_service_subscriptions
```

## Features Implemented

✅ **User Management**

- ایجاد کاربر خودکار از تلگرام
- موجودی کیف پول
- سطح دسترسی (admin flag)

✅ **Referral System**

- لینک دعوت یکتا
- شمارش کلیک و دعوت‌ها
- سیستم پاداش

✅ **Payment System**

- ایجاد درخواست پرداخت
- آپلود عکس فیش
- تصدیق توسط ادمین
- اضافه شدن خودکار به موجودی

✅ **Client Management**

- رجیستریشن کلاینت
- پیگیری میزان استفاده
- تغییر وضعیت

✅ **Service Packages**

- بسته‌های قابل خریداری
- تاریخ انقضا

## Running

```bash
# شروع دیتابیس
docker-compose up -d mysql phpmyadmin

# PHPMyAdmin در http://localhost:8080
# user: panel_user
# password: panel_pass_123
```
