import psycopg2
from tkinter import *
from tkinter import messagebox, ttk

# --- 1. VERİTABANI BAĞLANTISI ---
def db_baglan():
    return psycopg2.connect(
        dbname="Kutuphane.db",     
        user="postgres", 
        password="1234",        
        host="localhost", 
        port="5432"
    )

class KutuphaneSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("Kütüphane Yönetim Sistemi - Final v4.0")
        self.root.geometry("450x400")
        self.giris_ekrani()

    # --- GİRİŞ EKRANI ---
    def giris_ekrani(self):
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True)
        
        Label(self.main_frame, text="SİSTEM GİRİŞİ", font=("Arial", 14, "bold")).pack(pady=20)
        
        Label(self.main_frame, text="Kullanıcı Adı:").pack()
        self.ent_user = Entry(self.main_frame)
        self.ent_user.pack()
        
        Label(self.main_frame, text="Şifre:").pack()
        self.ent_pass = Entry(self.main_frame, show="*")
        self.ent_pass.pack()
        
        Button(self.main_frame, text="Giriş Yap", bg="#4CAF50", fg="white", width=20, command=self.login).pack(pady=20)

    def login(self):
        if self.ent_user.get() == "admin" and self.ent_pass.get() == "1234":
            self.main_frame.destroy()
            self.ana_menu_ekrani()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı!")

    # --- ANA MENÜ ---
    def ana_menu_ekrani(self):
        self.root.geometry("500x700")
        Label(self.root, text="ANA KONTROL PANELİ", font=("Arial", 16, "bold")).pack(pady=20)
        
        butonlar = [
            ("Üye Yönetimi (Ekle/Listele)", self.uye_ekrani),
            ("Kitap Yönetimi (Kategori/Yıl)", self.kitap_ekrani),
            ("Ödünç Verme İşlemi", self.odunc_ver_ekrani),
            ("İade Al & Ceza Hesapla", self.teslim_al_ekrani),
            ("Borç Ödeme İşlemi", self.borc_ode_ekrani), 
            ("Dinamik Sorgu (Detaylı Arama)", self.dinamik_sorgu_ekrani),
            ("İstatistiksel Raporlar", self.raporlar_ekrani),
            ("Çıkış", self.root.quit)
        ]
        
        for metin, komut in butonlar:
            Button(self.root, text=metin, width=45, height=2, command=komut).pack(pady=5)

    # --- ÜYE YÖNETİMİ ---
    def uye_ekrani(self):
        p = Toplevel(self.root)
        p.title("Gelişmiş Üye Yönetimi")
        p.geometry("900x550")

        f = Frame(p); f.pack(pady=10)

        Label(f, text="Ad:").grid(row=0, column=0, sticky=W)
        e_ad = Entry(f); e_ad.grid(row=0, column=1, padx=5, pady=2)
        
        Label(f, text="Soyad:").grid(row=0, column=2, sticky=W)
        e_soy = Entry(f); e_soy.grid(row=0, column=3, padx=5, pady=2)

        Label(f, text="Telefon:").grid(row=1, column=0, sticky=W)
        e_tel = Entry(f); e_tel.grid(row=1, column=1, padx=5, pady=2)

        Label(f, text="Email:").grid(row=1, column=2, sticky=W)
        e_mail = Entry(f); e_mail.grid(row=1, column=3, padx=5, pady=2)

        def temizle():
            e_ad.delete(0, END); e_soy.delete(0, END)
            e_tel.delete(0, END); e_mail.delete(0, END)

        def listele():
            for i in tree.get_children(): tree.delete(i)
            conn = db_baglan(); cur = conn.cursor()
            cur.execute("SELECT UyeID, Ad, Soyad, Telefon, Email, ToplamBorc FROM UYE ORDER BY UyeID DESC")
            for row in cur.fetchall(): tree.insert("", END, values=row)
            conn.close()

        def uye_ekle():
            if not e_ad.get() or not e_mail.get():
                messagebox.showwarning("Eksik Bilgi", "Ad ve Email zorunludur.")
                return
            try:
                conn = db_baglan(); cur = conn.cursor()
                cur.execute("INSERT INTO UYE (Ad, Soyad, Telefon, Email) VALUES (%s, %s, %s, %s)",
                            (e_ad.get(), e_soy.get(), e_tel.get(), e_mail.get()))
                conn.commit(); conn.close()
                messagebox.showinfo("Başarılı", "Yeni üye eklendi."); temizle(); listele()
            except Exception as e: messagebox.showerror("Hata", str(e))

        def uye_sil():
            secili = tree.selection()
            if not secili: return
            uye_id = tree.item(secili)['values'][0]
            
            # Burada kontrolü veritabanındaki TRIGGER'a bırakıyoruz.
            if messagebox.askyesno("Onay", "Üye silinecek. Emin misiniz?"):
                try:
                    conn = db_baglan(); cur = conn.cursor()
                    cur.execute("DELETE FROM UYE WHERE UyeID = %s", (uye_id,))
                    conn.commit(); conn.close()
                    listele()
                    messagebox.showinfo("Başarılı", "Üye silindi.")
                except Exception as e:
                    # Trigger hatası burada yakalanır
                    messagebox.showerror("ENGEL", f"Veritabanı İzni Vermedi:\n{e}")

        def uye_guncelle():
            secili = tree.selection()
            if not secili: return
            uye_id = tree.item(secili)['values'][0]
            conn = db_baglan(); cur = conn.cursor()
            cur.execute("UPDATE UYE SET Ad=%s, Soyad=%s, Telefon=%s, Email=%s WHERE UyeID=%s",
                        (e_ad.get(), e_soy.get(), e_tel.get(), e_mail.get(), uye_id))
            conn.commit(); conn.close(); listele(); messagebox.showinfo("Bilgi", "Güncellendi.")

        btn_frame = Frame(p); btn_frame.pack(pady=5)
        Button(btn_frame, text="Ekle", bg="#4CAF50", fg="white", width=10, command=uye_ekle).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Güncelle", bg="#2196F3", fg="white", width=10, command=uye_guncelle).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Sil", bg="#F44336", fg="white", width=10, command=uye_sil).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Temizle", command=temizle).pack(side=LEFT, padx=5)

        cols = ("ID", "Ad", "Soyad", "Telefon", "Email", "Borç")
        tree = ttk.Treeview(p, columns=cols, show='headings')
        for c in cols: tree.heading(c, text=c)
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        def secileni_doldur(event):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel)['values']
            temizle()
            e_ad.insert(0, vals[1]); e_soy.insert(0, vals[2])
            e_tel.insert(0, vals[3]); e_mail.insert(0, vals[4])
        tree.bind("<Double-1>", secileni_doldur)

        listele()

    # --- KİTAP YÖNETİMİ ---
    def kitap_ekrani(self):
        p = Toplevel(self.root); p.title("Kitap Yönetimi"); p.geometry("850x550")
        f = Frame(p); f.pack(pady=10)
        
        Label(f, text="Kitap Adı:").grid(row=0, column=0)
        e_ad = Entry(f); e_ad.grid(row=0, column=1)
        Label(f, text="Yazar:").grid(row=0, column=2)
        e_yaz = Entry(f); e_yaz.grid(row=0, column=3)
        Label(f, text="Basım Yılı:").grid(row=1, column=0)
        e_yil = Entry(f); e_yil.grid(row=1, column=1)
        Label(f, text="Kategori:").grid(row=1, column=2)
        
        conn = db_baglan(); cur = conn.cursor()
        cur.execute("SELECT DISTINCT KategoriAd FROM KATEGORI ORDER BY KategoriAd ASC")
        kats = [r[0] for r in cur.fetchall()]; conn.close()
        cb_kat = ttk.Combobox(f, values=kats); cb_kat.grid(row=1, column=3)

        cols = ("ID", "Kitap", "Yazar", "Kategori", "Yıl", "Stok")
        tree = ttk.Treeview(p, columns=cols, show='headings')
        for c in cols: tree.heading(c, text=c)
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        def listele():
            for i in tree.get_children(): tree.delete(i)
            conn = db_baglan(); cur = conn.cursor()
            sql = """SELECT k.KitapID, k.KitapAdi, k.Yazar, c.KategoriAd, k.BasimYili, k.MevcutAdet 
                     FROM KITAP k LEFT JOIN KATEGORI c ON k.KategoriID = c.KategoriID ORDER BY k.KitapID DESC"""
            cur.execute(sql)
            for r in cur.fetchall(): tree.insert("", END, values=r)
            conn.close()

        def ekle():
            try:
                conn = db_baglan(); cur = conn.cursor()
                cur.execute("SELECT KategoriID FROM KATEGORI WHERE KategoriAd=%s", (cb_kat.get(),))
                res = cur.fetchone()
                if not res: raise Exception("Kategori seçiniz!")
                kid = res[0]
                
                cur.execute("INSERT INTO KITAP (KitapAdi, Yazar, BasimYili, KategoriID, MevcutAdet, ToplamAdet) VALUES (%s,%s,%s,%s,5,5)",
                            (e_ad.get(), e_yaz.get(), e_yil.get(), kid))
                conn.commit(); conn.close(); listele(); messagebox.showinfo("Başarılı", "Kitap Eklendi")
            except Exception as e: messagebox.showerror("Hata", str(e))

        Button(f, text="Kitap Ekle", bg="orange", command=ekle).grid(row=0, column=4, rowspan=2, padx=10)
        listele()

    # --- ÖDÜNÇ VERME (PROSEDÜR KULLANIR) ---
    def odunc_ver_ekrani(self):
        p = Toplevel(self.root); p.geometry("350x300"); p.title("Ödünç Ver")
        
        Label(p, text="Üye ID:", font=("Arial", 10)).pack(pady=5)
        e_u = Entry(p); e_u.pack()
        
        Label(p, text="Kitap ID:", font=("Arial", 10)).pack(pady=5)
        e_k = Entry(p); e_k.pack()

        def ver():
            try:
                uye_id = int(e_u.get())
                kitap_id = int(e_k.get())

                conn = db_baglan(); cur = conn.cursor()
                cur.execute("CALL sp_YeniOduncVer(%s, %s)", (uye_id, kitap_id))
                
                conn.commit(); conn.close()
                messagebox.showinfo("Başarılı", "Kitap verildi. Stok otomatik düşüldü.")
                
            except ValueError: messagebox.showerror("Hata", "ID alanlarına sayı giriniz!")
            except Exception as e: 
                messagebox.showerror("İşlem Başarısız", f"Veritabanı Hatası:\n{e}")
        
        Button(p, text="Ödünç Ver", bg="green", fg="white", command=ver).pack(pady=20)

    # --- İADE ALMA (PROSEDÜR KULLANIR) ---
    def teslim_al_ekrani(self):
        p = Toplevel(self.root); p.title("İade ve Ceza"); p.geometry("700x450")
        
        Label(p, text="Aktif Ödünç Listesi (İade Bekleyenler)", font=("Arial", 10, "bold")).pack(pady=5)
        tree = ttk.Treeview(p, columns=("OduncID", "ÜyeID", "KitapID", "Son Tarih"), show='headings')
        for c in tree["columns"]: tree.heading(c, text=c)
        tree.pack(fill=BOTH, expand=True, padx=10)

        def listele():
            for i in tree.get_children(): tree.delete(i)
            conn = db_baglan(); cur = conn.cursor()
            cur.execute("SELECT OduncID, UyeID, KitapID, SonTeslimTarihi FROM ODUNC WHERE TeslimTarihi IS NULL")
            for r in cur.fetchall(): tree.insert("", END, values=r)
            conn.close()

        def iade():
            sel = tree.selection()
            if not sel: return
            oid = tree.item(sel)['values'][0]
            
            try:
                conn = db_baglan(); cur = conn.cursor()
                cur.execute("CALL sp_KitapTeslimAl(%s)", (oid,))
                
                conn.commit(); conn.close(); listele()
                messagebox.showinfo("Bilgi", "İade alındı.\nGecikme varsa ceza işlendi, stok artırıldı.")
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        Button(p, text="Seçili Kitabı İade Al", bg="red", fg="white", command=iade).pack(pady=10)
        listele()

    # ---BORÇ ÖDEME (3. PROSEDÜR) ---
    def borc_ode_ekrani(self):
        p = Toplevel(self.root); p.geometry("350x300"); p.title("Borç Ödeme")
        
        Label(p, text="Üye ID:", font=("Arial", 10)).pack(pady=5)
        e_uid = Entry(p); e_uid.pack()
        
        Label(p, text="Ödenecek Tutar (TL):", font=("Arial", 10)).pack(pady=5)
        e_tutar = Entry(p); e_tutar.pack()

        def ode():
            try:
                uid = int(e_uid.get())
                tutar = float(e_tutar.get())

                conn = db_baglan(); cur = conn.cursor()
                cur.execute("CALL sp_BorcOde(%s, %s)", (uid, tutar))
                
                conn.commit(); conn.close()
                messagebox.showinfo("Başarılı", f"{tutar} TL ödeme alındı.\nBakiye güncellendi.")
            except ValueError: messagebox.showerror("Hata", "Lütfen geçerli sayı giriniz!")
            except Exception as e: messagebox.showerror("Hata", f"İşlem Yapılamadı:\n{e}")

        Button(p, text="Borç Öde", bg="blue", fg="white", command=ode).pack(pady=20)

    # --- DİNAMİK SORGU ---
    def dinamik_sorgu_ekrani(self):
        p = Toplevel(self.root); p.title("Detaylı Arama"); p.geometry("900x600")
        f = Frame(p); f.pack(pady=10)
        Label(f, text="Kitap Adı:").grid(row=0, column=0)
        e_ad = Entry(f); e_ad.grid(row=0, column=1)
        Label(f, text="Min Yıl:").grid(row=0, column=2)
        e_yil = Entry(f); e_yil.grid(row=0, column=3)
        
        conn = db_baglan(); cur = conn.cursor(); cur.execute("SELECT DISTINCT KategoriAd FROM KATEGORI ORDER BY KategoriAd ASC")
        kats = ["Hepsi"] + [r[0] for r in cur.fetchall()]; conn.close()
        cb_kat = ttk.Combobox(f, values=kats); cb_kat.set("Hepsi"); cb_kat.grid(row=1, column=1)

        tree = ttk.Treeview(p, columns=("ID", "Kitap", "Yazar", "Kategori", "Yıl", "Stok"), show='headings')
        for c in tree["columns"]: tree.heading(c, text=c)
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        def ara():
            for i in tree.get_children(): tree.delete(i)
            sql = "SELECT k.KitapID, k.KitapAdi, k.Yazar, c.KategoriAd, k.BasimYili, k.MevcutAdet FROM KITAP k LEFT JOIN KATEGORI c ON k.KategoriID=c.KategoriID WHERE 1=1"
            params = []
            if e_ad.get(): sql+=" AND k.KitapAdi ILIKE %s"; params.append(f"%{e_ad.get()}%")
            if e_yil.get(): sql+=" AND k.BasimYili >= %s"; params.append(e_yil.get())
            if cb_kat.get()!="Hepsi": sql+=" AND c.KategoriAd=%s"; params.append(cb_kat.get())
            
            conn = db_baglan(); cur = conn.cursor(); cur.execute(sql, params)
            for r in cur.fetchall(): tree.insert("", END, values=r)
            conn.close()

        Button(p, text="Sorgula", bg="cyan", command=ara).pack(pady=10)

    # --- RAPORLAR ---
    def raporlar_ekrani(self):
        p = Toplevel(self.root); p.title("İstatistikler"); p.geometry("500x400")
        Label(p, text="En Çok Okunan Kitaplar", font=("Arial", 12)).pack(pady=10)
        
        tree = ttk.Treeview(p, columns=("Kitap", "Okunma Sayısı"), show='headings')
        tree.heading("Kitap", text="Kitap"); tree.heading("Okunma Sayısı", text="Okunma Sayısı")
        tree.pack(fill=BOTH, expand=True, padx=10)

        conn = db_baglan(); cur = conn.cursor()
        cur.execute("SELECT k.KitapAdi, COUNT(o.OduncID) FROM ODUNC o JOIN KITAP k ON o.KitapID=k.KitapID GROUP BY k.KitapAdi ORDER BY 2 DESC")
        for r in cur.fetchall(): tree.insert("", END, values=r)
        conn.close()

if __name__ == "__main__":
    root = Tk()
    app = KutuphaneSistemi(root)
    root.mainloop()