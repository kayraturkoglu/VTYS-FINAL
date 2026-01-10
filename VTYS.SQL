-- 1. TABLOLAR
CREATE TABLE LOG_ISLEM (
    LogID SERIAL PRIMARY KEY,
    TabloAdi VARCHAR(50),
    IslemTuru VARCHAR(20),
    IslemZamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Aciklama TEXT
);

CREATE TABLE KATEGORI (
    KategoriID SERIAL PRIMARY KEY,
    KategoriAd VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE UYE (
    UyeID SERIAL PRIMARY KEY,
    Ad VARCHAR(50) NOT NULL,
    Soyad VARCHAR(50) NOT NULL,
    Telefon VARCHAR(20),
    Email VARCHAR(100) UNIQUE,
    ToplamBorc NUMERIC DEFAULT 0,
    KayitTarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE KITAP (
    KitapID SERIAL PRIMARY KEY,
    KitapAdi VARCHAR(100) NOT NULL,
    Yazar VARCHAR(100),
    BasimYili INT,
    KategoriID INT REFERENCES KATEGORI(KategoriID),
    MevcutAdet INT DEFAULT 0,
    ToplamAdet INT DEFAULT 0,
    EklemeTarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ODUNC (
    OduncID SERIAL PRIMARY KEY,
    UyeID INT REFERENCES UYE(UyeID),
    KitapID INT REFERENCES KITAP(KitapID),
    OduncTarihi DATE DEFAULT CURRENT_DATE,
    SonTeslimTarihi DATE NOT NULL,
    TeslimTarihi DATE
);

-- 2. TRIGGER FONKSİYONLARI
CREATE OR REPLACE FUNCTION fn_OduncEkle_StokDus() RETURNS TRIGGER AS $$
BEGIN
    UPDATE KITAP SET MevcutAdet = MevcutAdet - 1 WHERE KitapID = NEW.KitapID;
    INSERT INTO LOG_ISLEM (TabloAdi, IslemTuru, Aciklama)
    VALUES ('ODUNC', 'INSERT', 'Kitap ödünç verildi. KitapID: ' || NEW.KitapID);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_OduncTeslim_StokArtir() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.TeslimTarihi IS NULL AND NEW.TeslimTarihi IS NOT NULL THEN
        UPDATE KITAP SET MevcutAdet = MevcutAdet + 1 WHERE KitapID = NEW.KitapID;
        INSERT INTO LOG_ISLEM (TabloAdi, IslemTuru, Aciklama)
        VALUES ('ODUNC', 'UPDATE', 'Kitap iade alındı. OduncID: ' || NEW.OduncID);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_UyeSilmeKontrol() RETURNS TRIGGER AS $$
DECLARE
    v_AktifKitap INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_AktifKitap FROM ODUNC WHERE UyeID = OLD.UyeID AND TeslimTarihi IS NULL;
    
    IF v_AktifKitap > 0 THEN
        RAISE EXCEPTION 'Bu üyenin teslim etmediği kitaplar var, silinemez!';
    ELSIF OLD.ToplamBorc > 0 THEN
        RAISE EXCEPTION 'Bu üyenin borcu var, silinemez!';
    END IF;

    INSERT INTO LOG_ISLEM (TabloAdi, IslemTuru, Aciklama)
    VALUES ('UYE', 'DELETE', 'Üye silindi. UyeID: ' || OLD.UyeID);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- 3. TRIGGER TANIMLARI
CREATE TRIGGER tr_OduncEkle AFTER INSERT ON ODUNC FOR EACH ROW EXECUTE PROCEDURE fn_OduncEkle_StokDus();
CREATE TRIGGER tr_OduncTeslim AFTER UPDATE ON ODUNC FOR EACH ROW EXECUTE PROCEDURE fn_OduncTeslim_StokArtir();
CREATE TRIGGER tr_UyeSil BEFORE DELETE ON UYE FOR EACH ROW EXECUTE PROCEDURE fn_UyeSilmeKontrol();

-- 4. SAKLI YORDAMLAR (STORED PROCEDURES)

-- 4.1. Ödünç Verme
CREATE OR REPLACE PROCEDURE sp_YeniOduncVer(p_UyeID INTEGER, p_KitapID INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_Stok INTEGER;
BEGIN
    SELECT MevcutAdet INTO v_Stok FROM KITAP WHERE KitapID = p_KitapID;
    IF v_Stok IS NULL THEN RAISE EXCEPTION 'Kitap bulunamadı!';
    ELSIF v_Stok <= 0 THEN RAISE EXCEPTION 'Stok tükendi!';
    END IF;
    INSERT INTO ODUNC (UyeID, KitapID, OduncTarihi, SonTeslimTarihi)
    VALUES (p_UyeID, p_KitapID, CURRENT_DATE, CURRENT_DATE + INTERVAL '15 days');
END;
$$;

-- 4.2. İade Alma
CREATE OR REPLACE PROCEDURE sp_KitapTeslimAl(p_OduncID INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_SonTarih DATE;
    v_GecikmeGun INTEGER;
    v_CezaMiktari NUMERIC := 0;
    v_UyeID INTEGER;
BEGIN
    SELECT SonTeslimTarihi, UyeID INTO v_SonTarih, v_UyeID FROM ODUNC WHERE OduncID = p_OduncID;
    UPDATE ODUNC SET TeslimTarihi = CURRENT_DATE WHERE OduncID = p_OduncID;
    IF CURRENT_DATE > v_SonTarih THEN
        v_GecikmeGun := CURRENT_DATE - v_SonTarih;
        v_CezaMiktari := v_GecikmeGun * 2.0;
        UPDATE UYE SET ToplamBorc = ToplamBorc + v_CezaMiktari WHERE UyeID = v_UyeID;
        INSERT INTO LOG_ISLEM (TabloAdi, IslemTuru, Aciklama) 
        VALUES ('CEZA', 'INSERT', 'Gecikme cezası. Tutar: ' || v_CezaMiktari);
    END IF;
END;
$$;

-- 4.3. BORÇ ÖDEME (3. PROSEDÜR)
CREATE OR REPLACE PROCEDURE sp_BorcOde(p_UyeID INTEGER, p_Miktar NUMERIC)
LANGUAGE plpgsql
AS $$
DECLARE
    v_MevcutBorc NUMERIC;
BEGIN
    -- Üyenin borcunu kontrol et
    SELECT ToplamBorc INTO v_MevcutBorc FROM UYE WHERE UyeID = p_UyeID;
    
    IF v_MevcutBorc IS NULL THEN 
        RAISE EXCEPTION 'Üye bulunamadı!';
    ELSIF p_Miktar <= 0 THEN
        RAISE EXCEPTION 'Ödenecek miktar 0 dan büyük olmalı!';
    END IF;

    -- Borcu düş
    UPDATE UYE SET ToplamBorc = ToplamBorc - p_Miktar WHERE UyeID = p_UyeID;

    -- Log Kaydı
    INSERT INTO LOG_ISLEM (TabloAdi, IslemTuru, Aciklama)
    VALUES ('UYE', 'UPDATE', 'Borç ödendi. UyeID: ' || p_UyeID || ', Tutar: ' || p_Miktar);
END;
$$;

