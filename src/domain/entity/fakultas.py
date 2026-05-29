"""Reference data: IPB fakultas and their departemen.

Used to guard registration so only valid fakultas/departemen pairs are accepted.
"""

# fakultas -> list of departemen
FAKULTAS_DEPARTEMEN: dict[str, list[str]] = {
    "Fakultas Pertanian": [
        "Manajemen Sumberdaya Lahan",
        "Agronomi dan Hortikultura",
        "Proteksi Tanaman",
        "Arsitektur Lanskap",
        "Smart Agriculture",
    ],
    "Fakultas Perikanan dan Ilmu Kelautan": [
        "Teknologi dan Manajemen Perikanan Budidaya",
        "Manajemen Sumberdaya Perairan",
        "Teknologi Hasil Perairan",
        "Teknologi dan Manajemen Perikanan Tangkap",
        "Ilmu dan Teknologi Kelautan",
    ],
    "Fakultas Peternakan": [
        "Teknologi Produksi Ternak",
        "Nutrisi dan Teknologi Pakan",
        "Teknologi Hasil Ternak",
    ],
    "Fakultas Kehutanan dan Lingkungan": [
        "Manajemen Hutan",
        "Teknologi Hasil Hutan",
        "Konservasi Sumberdaya Hutan & Ekowisata",
        "Silvikultur",
    ],
    "Fakultas Teknik dan Teknologi": [
        "Teknik Pertanian dan Biosistem",
        "Teknologi Pangan",
        "Teknik Industri Pertanian",
        "Teknik Sipil dan Lingkungan",
        "Teknik Mesin",
        "Teknik Kimia",
    ],
    "Fakultas Matematika dan Ilmu Pengetahuan Alam": [
        "Meteorologi Terapan",
        "Biologi",
        "Kimia",
        "Fisika",
        "Biokimia",
        "Bioinformatika",
    ],
    "Fakultas Ekonomi dan Manajemen": [
        "Ekonomi Pembangunan",
        "Manajemen",
        "Agribisnis",
        "Ekonomi Sumberdaya dan Lingkungan",
        "Ilmu Ekonomi Syariah",
    ],
    "Fakultas Ekologi Manusia": [
        "Ilmu Keluarga dan Konsumen",
        "Komunikasi dan Pengembangan Masyarakat",
    ],
    "Fakultas Kedokteran dan Gizi": [
        "Kedokteran",
        "Ilmu Gizi",
    ],
    "Sekolah Bisnis": [
        "Bisnis",
    ],
    "Sekolah Kedokteran Hewan dan Biomedis": [
        "Kedokteran Hewan",
        "Sains Biomedis",
    ],
    "Sekolah Sains Data, Matematika, dan Informatika": [
        "Statistika dan Sains Data",
        "Matematika",
        "Ilmu Komputer",
        "Aktuaria",
        "Kecerdasan Buatan",
    ],
}


def is_valid_fakultas(fakultas: str) -> bool:
    return fakultas in FAKULTAS_DEPARTEMEN


def is_valid_departemen(fakultas: str, departemen: str) -> bool:
    return departemen in FAKULTAS_DEPARTEMEN.get(fakultas, [])


def list_fakultas() -> list[str]:
    return list(FAKULTAS_DEPARTEMEN.keys())


def list_departemen(fakultas: str) -> list[str] | None:
    """Return departemen for a fakultas, or None if fakultas not found."""
    return FAKULTAS_DEPARTEMEN.get(fakultas)
