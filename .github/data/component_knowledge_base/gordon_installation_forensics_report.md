# Gordon Installation Forensics Report

- Install root: `C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY`
- DB copy: `C:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\data fra gordon\GordonsReloadingTool.db`
- DB size: `101105664` bytes

## Key Findings

- `REALSQLDatabase` present: `True`
- encryption API present: `True`
- attach-with-key API present: `True`
- CIP URL present: `True`
- SAAMI URL present: `False`
- SAAMI standard token present in exe: `True`
- user XML dump functions present: `True`
- native open exchange formats documented: `projectilefile`, `propellantfile`, `caliberfile`
- native Gordon file extensions documented: `*.projectile`, `*.propellant`, `*.caliber`

## Interpretation

- **projectile**: Built-in projectile catalog exists in Gordon and uses an internal SQL schema. The public docs only describe exporting selected projectile records to XML and user XML backups.
- **propellant**: Built-in propellant catalog exists in Gordon and includes full powder-model fields such as Ba, Qex, k, eta, a0, z1, z2, pc, pcd, pt, tcc and tch.
- **caliber**: Built-in caliber catalog is strongly CIP-oriented in this nightly build. Schema and strings expose CIP fields and CIP datasheet URL handling. A `SAAMI` standard token exists internally, but no SAAMI URL handling was found, so CIP still appears to be the dominant official datasheet path.
- **db**: The .db file is almost certainly a SQL-backed encrypted database rather than a plain SQLite file. The executable exposes REALSQLDatabase encryption APIs and SQL table definitions.

## 2026-03-31 Follow-up

- The install ships a separate `libs\sqlite.dll`, but a quick export scan did **not** show obvious public crypto functions like `sqlite3_key` or `sqlite3_rekey`.
- A combined intake run from install root plus `%APPDATA%\GordonsReloadingTool` produced:
  - `14` raw projectile rows
  - `8` raw propellant rows
  - `8` raw caliber rows
- AppData currently contains:
  - `projectile.xml`: present
  - `propellant.xml`: missing
  - `caliber.xml`: missing
- New evidence from executable strings:
  - `XmlUserFileDumpProjectile`
  - `XmlUserFileDumpPropellant`
  - `XmlUserFileDumpCaliber`
  - `SqlDumpTable`
  - `SqlDump`
  - `ConvertToMySQL`

These findings strengthen two paths:

- **XML/export path**: clearly supported and now fully documented in GRT's own docs
- **internal dump path**: there are strong signs Gordon has internal SQL dump helpers, but we do not yet have a supported way to trigger them externally

## SQL Schema Extracts

### caliber
```sql
CREATE TABLE caliber (  id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,  cipname         TEXT NOT NULL,  altname         TEXT NOT NULL,  standard        TEXT NOT NULL,  ciporigin       TEXT NOT NULL,  ciptype         TEXT NOT NULL,  cipdate         DATE NOT NULL,  ciprevdate      DATE NOT NULL,  cippdf          TEXT NOT NULL,  L0              FLOAT NOT NULL,  L1              FLOAT NOT NULL,  L2              FLOAT NOT NULL,  L3              FLOAT NOT NULL,  L4              FLOAT NOT NULL,  L5              FLOAT NOT NULL,  L6              FLOAT NOT NULL,  R              FLOAT NOT NULL,  R1              FLOAT NOT NULL,  R3              FLOAT NOT NULL,  E               FLOAT NOT NULL,  E1              FLOAT NOT NULL,  Emin            FLOAT NOT NULL,  delta           TEXT NOT NULL,  FG              FLOAT NOT NULL,  beta            TEXT NOT NULL,  P0              FLOAT NOT NULL,  P1              FLOAT NOT NULL,  P2              FLOAT NOT NULL,  alpha           TEXT NOT NULL,  S               FLOAT NOT NULL,  r1min           FLOAT NOT NULL,  r2              FLOAT NOT NULL,  H1              FLOAT NOT NULL,  H2              FLOAT NOT NULL,  G1              FLOAT NOT NULL,  G2              FLOAT NOT NULL,  f               FLOAT NOT NULL,  L3G             FLOAT NOT NULL,  Pmax            FLOAT NOT NULL,  PK              FLOAT NOT NULL,  PE              FLOAT NOT NULL,  EE              FLOAT NOT NULL,  V               FLOAT NOT NULL,  M               TEXT NOT NULL,  c_L0              FLOAT NOT NULL,  c_L1              FLOAT NOT NULL,  c_L2              FLOAT NOT NULL,  c_L3              FLOAT NOT NULL,  c_R              FLOAT NOT NULL,  c_R1              FLOAT NOT NULL,  c_R2              FLOAT NOT NULL,  c_R3              FLOAT NOT NULL,  c_r_             FLOAT NOT NULL,  c_E                FLOAT NOT NULL,  c_P0              FLOAT NOT NULL,  c_P1              FLOAT NOT NULL,  c_P2              FLOAT NOT NULL,  c_alpha         FLOAT NOT NULL,  c_S              FLOAT NOT NULL,  c_r1max      FLOAT NOT NULL,  c_r2_           FLOAT NOT NULL,  c_H1              FLOAT NOT NULL,  c_H2              FLOAT NOT NULL,  c_G              FLOAT NOT NULL,  c_G1              FLOAT NOT NULL,  c_alpha1       FLOAT NOT NULL,  c_h_             FLOAT NOT NULL,  c_s_              FLOAT NOT NULL,  c_i_              FLOAT NOT NULL,  c_w_             FLOAT NOT NULL,  c_F               FLOAT NOT NULL,  c_Z               FLOAT NOT NULL,  c_b_              FLOAT NOT NULL,  c_N               FLOAT NOT NULL,  c_u_               FLOAT NOT NULL,  c_Q               FLOAT NOT NULL,  c_delta         FLOAT NOT NULL,  c_Fe             FLOAT NOT NULL,  c_Fe_proof      FLOAT NOT NULL,  c_Fe_auto       FLOAT NOT NULL,  sebert          FLOAT NOT NULL,  cdate           DATE NOT NULL,  cby             TEXT NOT NULL,  mdate           DATE NOT NULL,  mby             TEXT NOT NULL,  type            TEXT NOT NULL,  mode            TEXT NOT NULL,  status          TEXT NOT NULL,  origin          TEXT NOT NULL,  descr           TEXT NOT NULL,  geloescht       INTEGER NOT NULL);
```

### projectile
```sql
CREATE TABLE projectile (  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,  mname     TEXT COLLATE NOCASE NOT NULL,  pname     TEXT COLLATE NOCASE NOT NULL,  lotid     TEXT COLLATE NOCASE NOT NULL,  caliber   TEXT COLLATE NOCASE NOT NULL,  gdia      FLOAT NOT NULL,  glen      FLOAT NOT NULL,  gmass     FLOAT NOT NULL,  gpressure FLOAT NOT NULL,  gfriction FLOAT NOT NULL,  gtaildiaA FLOAT NOT NULL,  gtaildiaB FLOAT NOT NULL,  gtailh    FLOAT NOT NULL,  gtailtype INTEGER NOT NULL,  gdepthmax      FLOAT NOT NULL,  g1bc      FLOAT NOT NULL,  g7bc      FLOAT NOT NULL,  gUBCS     TEXT COLLATE NOCASE NOT NULL,  cdate     DATE NOT NULL,  cby       TEXT COLLATE NOCASE NOT NULL,  mdate     DATE NOT NULL,  mby       TEXT COLLATE NOCASE NOT NULL,  type      TEXT COLLATE NOCASE NOT NULL,  mode      TEXT COLLATE NOCASE NOT NULL,  status    TEXT COLLATE NOCASE NOT NULL,  origin    TEXT COLLATE NOCASE NOT NULL,  descr     TEXT COLLATE NOCASE NOT NULL,  imageUuid     TEXT NOT NULL,  geloescht INTEGER NOT NULL);
```

### propellant
```sql
CREATE TABLE propellant (	id				INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,	mname			TEXT COLLATE NOCASE NOT NULL,	pname			TEXT COLLATE NOCASE NOT NULL,	lotid			TEXT COLLATE NOCASE NOT NULL,	Br				FLOAT NOT NULL,	Bp				FLOAT NOT NULL,	Brp				FLOAT NOT NULL,	Ba				FLOAT NOT NULL,	Qex				FLOAT NOT NULL,	k					FLOAT NOT NULL,	eta				FLOAT NOT NULL,	a0				FLOAT NOT NULL,	a1				FLOAT NOT NULL,	z1				FLOAT NOT NULL,	z2				FLOAT NOT NULL,	pc				FLOAT NOT NULL,	pcd				FLOAT NOT NULL,	pt				FLOAT NOT NULL,	tcc				FLOAT NOT NULL,	tch				FLOAT NOT NULL,	Lp				FLOAT NOT NULL,	Lr				FLOAT NOT NULL,	L01				FLOAT NOT NULL,	L02				FLOAT NOT NULL,	L03				FLOAT NOT NULL,	L04				FLOAT NOT NULL,	L05				FLOAT NOT NULL,	L06				FLOAT NOT NULL,	L07				FLOAT NOT NULL,	L08				FLOAT NOT NULL,	L09				FLOAT NOT NULL,	Qlty			FLOAT NOT NULL,	cdate			DATE NOT NULL,	cby				TEXT COLLATE NOCASE NOT NULL,	mdate			DATE NOT NULL,	mby				TEXT COLLATE NOCASE NOT NULL,	type			TEXT COLLATE NOCASE NOT NULL,	mode			TEXT COLLATE NOCASE NOT NULL,	status		TEXT COLLATE NOCASE NOT NULL,	origin		TEXT COLLATE NOCASE NOT NULL,	descr			TEXT COLLATE NOCASE NOT NULL,	imageUuid	TEXT NOT NULL,	imageDetailUuid	TEXT NOT NULL,	geloescht	INTEGER NOT NULL);
```

## Next Steps

- Prefer building our own database from extracted Gordon schema plus official CIP/SAAMI/manufacturer data.
- Attempt UI automation or internal command discovery for bulk export, because docs only expose single-record export.
- Investigate whether the Gordon executable can be coerced to dump user XML for built-in records or expose a hidden database maintenance action.
- Treat SAAMI as a separate ingestion track because this Gordon build shows strong CIP evidence but no SAAMI URL evidence.
