# Simulasi Algoritma dan Evaluasi

Dokumentasi ini menjelaskan langkah-langkah untuk menyiapkan lingkungan kerja dan menjalankan program simulasi eksperimen algoritma hingga pembuatan grafik hasil.

## Langkah-Langkah Menjalankan Simulasi

### 1. Persiapan Lingkungan (Setup)

Pastikan sistem Anda sudah terperbarui dan memiliki perangkat lunak yang diperlukan.

* **Update Paket:**
    Perbarui daftar paket pada sistem Anda.
    ```bash
    sudo apt update
    ```

* **Install Python dan Pip:**
    Pasang Python 3 beserta pengelola paket pip.
    ```bash
    sudo apt install python3 python3-pip
    ```

* **Aktifkan Virtual Environment:**
    Gunakan lingkungan virtual agar instalasi library tetap terisolasi.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

* **Install Requirements:**
    Pasang semua pustaka (dependencies) yang dibutuhkan.
    ```bash
    pip install -r requirements.txt
    ```

---

### 2. Eksekusi Program

Jalankan perintah berikut secara berurutan untuk memproses simulasi:

#### A. Membuat DAG
Langkah pertama adalah membuat *Directed Acyclic Graph* (DAG) menggunakan generator.
```bash
python dag_generator.py
