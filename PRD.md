# Penjelasan kolom
1. Informasi Dasar & Tipe Hotel
hotel: Tipe hotel yang dipesan (pilihannya biasanya antara Resort Hotel atau City Hotel).

is_canceled: Status apakah pesanan dibatalkan atau tidak.

0 = Tidak batal (tamu datang).

1 = Batal (canceled).

2. Informasi Waktu Kedatangan (Arrival)
lead_time: Jumlah hari antara tanggal pemesanan (booking) dan tanggal kedatangan.

arrival_date_year: Tahun kedatangan (misal: 2015).

arrival_date_month: Bulan kedatangan (misal: July).

arrival_date_week_number: Nomor minggu dalam setahun untuk kedatangan (minggu ke-1 sampai ke-53).

arrival_date_day_of_month: Tanggal kedatangan (angka 1 sampai 31).

3. Detail Masa Menginap & Tamu
stays_in_weekend_nights: Jumlah malam tamu menginap pada akhir pekan (Sabtu atau Minggu malam).

stays_in_week_nights: Jumlah malam tamu menginap pada hari kerja (Senin sampai Jumat malam).

adults: Jumlah orang dewasa dalam satu pesanan.

children: Jumlah anak-anak.

babies: Jumlah bayi.

4. Preferensi & Profil Tamu
meal: Tipe paket makanan yang dipesan.

BB = Bed & Breakfast (Hanya sarapan).

HB = Half Board (Sarapan dan satu makan besar lain, biasanya makan malam).

FB = Full Board (Sarapan, makan siang, dan makan malam).

SC atau Undefined = Self-Catering (Tanpa paket makanan).

country: Negara asal tamu (menggunakan kode negara 3 huruf ISO, misal PRT untuk Portugal, FRA untuk Prancis).

market_segment: Segmen pasar pemesan (misal: Direct = pesan langsung, Online TA = Travel Agent Online, Corporate = Perusahaan).

distribution_channel: Saluran yang digunakan untuk memesan (misal: Direct, TA/TO = Travel Agent/Tour Operator, Corporate).

5. Riwayat / Loyalitas Tamu
is_repeated_guest: Apakah tamu ini pernah menginap di sini sebelumnya? (0 = Tidak, 1 = Ya).

previous_cancellations: Jumlah pesanan yang pernah dibatalkan oleh tamu ini di masa lalu sebelum pesanan saat ini.

previous_bookings_not_canceled: Jumlah pesanan yang sukses/tidak dibatalkan oleh tamu ini di masa lalu.

6. Detail Kamar & Keuangan
reserved_room_type: Kode tipe kamar yang dipesan awal oleh tamu (dinyatakan dalam kode huruf seperti A, B, C, dst).

assigned_room_type: Kode tipe kamar yang akhirnya diberikan oleh hotel saat check-in. Kadang berbeda dengan yang dipesan karena alasan upgrade atau kamar penuh.

booking_changes: Jumlah perubahan/revisi yang dilakukan tamu pada pesanannya (misal mengubah tanggal, menambah kamar) sebelum check-in.

deposit_type: Jenis jaminan uang muka yang diberikan tamu.

No Deposit = Tanpa uang muka.

Non Refund = Uang muka penuh dan tidak bisa dikembalikan jika batal.

Refundable = Uang muka bisa dikembalikan.

agent: ID agen perjalanan yang melakukan pemesanan (jika lewat agen).

company: ID perusahaan yang memesan/membayar kamar (jika berupa pesanan korporat).

adr: Average Daily Rate (Rata-rata harga sewa kamar per hari).

7. Informasi Tambahan & Status Akhir
days_in_waiting_list: Jumlah hari pesanan berada di daftar tunggu (waiting list) sebelum akhirnya dikonfirmasi oleh hotel.

customer_type: Tipe pelanggan.

Transient = Tamu perorangan/mandiri.

Transient-Party = Tamu perorangan tapi bagian dari grup tertentu.

Contract = Tamu yang terikat kontrak (seperti kru maskapai).

Group = Tamu rombongan.

required_car_parking_spaces: Jumlah tempat parkir mobil yang diminta oleh tamu.

total_of_special_requests: Jumlah permintaan khusus dari tamu (misal: minta kasur tipe twin, kamar di lantai tinggi, atau kamar bebas asap rokok).

reservation_status: Status terakhir dari reservasi tersebut.

Check-Out = Tamu sudah datang dan sudah pulang.

Canceled = Pesanan dibatalkan.

No-Show = Tamu tidak datang tanpa kabar.

reservation_status_date: Tanggal kapan status terakhir (reservation_status) dicatat atau diperbarui.