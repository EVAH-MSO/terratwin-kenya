from app.db import get_connection

# The 47 counties of Kenya with approximate centroid coordinates and capital
COUNTIES = [
    ("001", "Mombasa",     "Mombasa",     1208333, 212.5,   -4.0547, 39.6673),
    ("002", "Kwale",       "Kwale",        866820, 8270.3,  -4.1737, 39.4521),
    ("003", "Kilifi",      "Kilifi",      1453787, 12245.9, -3.5107, 39.9093),
    ("004", "Tana River",  "Hola",         315943, 35375.8, -1.4988, 39.9955),
    ("005", "Lamu",        "Lamu",         143920, 6497.7,  -2.2717, 40.9020),
    ("006", "Taita Taveta","Voi",          340671, 17083.9, -3.3167, 38.4833),
    ("007", "Garissa",     "Garissa",      841353, 45720.2, -0.4536, 39.6583),
    ("008", "Wajir",       "Wajir",        781263, 55840.6,  1.7471, 40.0573),
    ("009", "Mandera",     "Mandera",     1200000, 25797.7,  3.9373, 41.8670),
    ("010", "Marsabit",    "Marsabit",    459785, 66923.1,   2.3340, 37.9899),
    ("011", "Isiolo",      "Isiolo",      268002, 25336.1,   0.3546, 37.5822),
    ("012", "Meru",        "Meru",       1545714, 6936.2,    0.0500, 37.6500),
    ("013", "Tharaka-Nithi","Kathwana",   393177, 2609.5,   -0.3000, 37.9000),
    ("014", "Embu",        "Embu",        608599, 2555.9,   -0.5392, 37.4574),
    ("015", "Kitui",       "Kitui",      1136187, 24385.1,  -1.3667, 38.0167),
    ("016", "Machakos",    "Machakos",   1421932, 6208.2,   -1.5177, 37.2650),
    ("017", "Makueni",     "Wote",       1189923, 8008.9,   -1.7833, 37.6167),
    ("018", "Nyandarua",   "Ol Kalou",    638289, 3107.7,   -0.2667, 36.3833),
    ("019", "Nyeri",       "Nyeri",       759164, 2361.0,   -0.4167, 36.9500),
    ("020", "Kirinyaga",   "Kerugoya",    610411, 1205.4,   -0.4989, 37.2803),
    ("021", "Murang'a",    "Murang'a",   1056640, 2325.8,   -0.7167, 37.1500),
    ("022", "Kiambu",      "Kiambu",     2417733, 2449.2,   -1.0269, 36.6500),
    ("023", "Turkana",     "Lodwar",      926976, 71597.8,   3.1167, 35.6000),
    ("024", "West Pokot",  "Kapenguria",  621241, 8418.2,    1.2333, 35.1167),
    ("025", "Samburu",     "Maralal",     310327, 21000.4,   1.0968, 36.6980),
    ("026", "Trans Nzoia","Kitale",       990341, 2469.6,    1.0167, 35.0000),
    ("027", "Uasin Gishu","Eldoret",     1163186, 2955.3,    0.5143, 35.2698),
    ("028", "Elgeyo-Marakwet","Iten",     454480, 3049.6,    0.6700, 35.5100),
    ("029", "Nandi",       "Kapsabet",    885711, 2884.5,    0.2020, 35.1020),
    ("030", "Baringo",     "Kabarnet",    666763, 11075.3,   0.4939, 35.7430),
    ("031", "Laikipia",    "Nanyuki",     518560, 9462.4,    0.0167, 37.0667),
    ("032", "Nakuru",      "Nakuru",     2162202, 7509.5,   -0.2867, 36.0667),
    ("033", "Narok",       "Narok",      1157873, 17921.2,  -1.0833, 35.8667),
    ("034", "Kajiado",     "Kajiado",    1117840, 21292.7,  -1.8500, 36.7833),
    ("035", "Kericho",     "Kericho",     901777, 2454.5,   -0.3667, 35.2833),
    ("036", "Bomet",       "Bomet",       875689, 1997.9,   -0.7833, 35.3417),
    ("037", "Kakamega",    "Kakamega",   1867579, 3033.8,    0.2827, 34.7519),
    ("038", "Vihiga",      "Mbale",       590013, 531.3,     0.0500, 34.7167),
    ("039", "Bungoma",     "Bungoma",    1670570, 2068.6,    0.5635, 34.5606),
    ("040", "Busia",       "Busia",       893681, 1628.4,    0.4608, 34.1115),
    ("041", "Siaya",       "Siaya",       993183, 2530.7,    0.0615, 34.2882),
    ("042", "Kisumu",      "Kisumu",     1155574, 2085.9,   -0.0917, 34.7680),
    ("043", "Homa Bay",    "Homa Bay",   1131950, 3154.7,   -0.5273, 34.4571),
    ("044", "Migori",      "Migori",     1116436, 2586.4,   -1.0634, 34.4731),
    ("045", "Kisii",       "Kisii",      1266860, 1317.9,   -0.6817, 34.7680),
    ("046", "Nyamira",     "Nyamira",     605576, 912.5,    -0.5633, 34.9358),
    ("047", "Nairobi",     "Nairobi",    4397073, 696.1,    -1.2864, 36.8172),
]

def load_counties():
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM counties")

    for c in COUNTIES:
        cursor.execute(
            "INSERT INTO counties (code, name, capital, population, area_km2, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (c[0], c[1], c[2], c[3], c[4], c[5], c[6])
        )

    conn.close()
    print(f"✅ Loaded {len(COUNTIES)} counties into Azure SQL")

if __name__ == "__main__":
    load_counties()