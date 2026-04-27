# Gordon Hidden Capabilities Report

- Install root: `C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY`
- Exe path: `C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool.exe`
- Expected AppData root: `C:\Users\bjjoh\AppData\Roaming\GordonsReloadingTool`

## Summary

- `has_internal_sql_dump`: `True`
- `has_xml_dump_routines`: `True`
- `has_xml_import_routines`: `True`
- `has_db_key_attach`: `True`
- `cip_datasheet_support`: `True`
- `saami_standard_token_present`: `True`
- `native_component_tags_present`: `True`

## PDF Manuals

- `grt-manual-2021-09-29-de.pdf` (13517944 bytes)
- `grt-manual-2021-09-29-en.pdf` (13664013 bytes)
- `grt-manual-2021-09-29-fr.pdf` (13699368 bytes)
- `grt-manual-2021-09-29-ru.pdf` (13694134 bytes)
- `grt-manual-2021-09-29-uk.pdf` (11730838 bytes)

## Capability Hits

### sql_dump_table
- needle: `SqlDumpTable`
- present: `True`
- index: `25498454`
```text
FindCaliberFromName                             %o<InnerBallistikCaliber>%sb                            FindProjectileFromName                          %o<InnerBallistikProjectile>%s                          SqlDumpTable                            SqlDump                             ConvertToMySQL                          XmlUserFileDump                             XmlUserFileImportPropellant                             XmlU
```

### sql_dump
- needle: `SqlDump`
- present: `True`
- index: `25498454`
```text
FindCaliberFromName                             %o<InnerBallistikCaliber>%sb                            FindProjectileFromName                          %o<InnerBallistikProjectile>%s                          SqlDumpTable                            SqlDump                             ConvertToMySQL                          XmlUserFileDump                             XmlUserFileImportPropellant                             XmlU
```

### convert_to_mysql
- needle: `ConvertToMySQL`
- present: `True`
- index: `25498530`
```text
kCaliber>%sb                            FindProjectileFromName                          %o<InnerBallistikProjectile>%s                          SqlDumpTable                            SqlDump                             ConvertToMySQL                          XmlUserFileDump                             XmlUserFileImportPropellant                             XmlUserFileImportProjectile                             XmlUserFileImportCaliber
```

### xml_dump_projectile
- needle: `XmlUserFileDumpProjectile`
- present: `True`
- index: `25500918`
```text
BallistikProjectile>%o<InnerBallistikProjectile>b                           XmlUserFileImport                           XmlUserFileDumpPropellant                           XmlUserFileDumpCaliber                          XmlUserFileDumpProjectile                           XmlUserFileDumpGun                          \tmp\20211008\innereBallistik              (           (e:\projekte\innereBallistik\Tools\grtdb-
```

### xml_dump_propellant
- needle: `XmlUserFileDumpPropellant`
- present: `True`
- index: `25500818`
```text
onary>%                             GetProjectileDuplicateCount                9           9%o<InnerBallistikProjectile>%o<InnerBallistikProjectile>b                           XmlUserFileImport                           XmlUserFileDumpPropellant                           XmlUserFileDumpCaliber                          XmlUserFileDumpProjectile                           XmlUserFileDumpGun                          \tmp\20211008\innereBall
```

### xml_dump_caliber
- needle: `XmlUserFileDumpCaliber`
- present: `True`
- index: `25500870`
```text
licateCount                9           9%o<InnerBallistikProjectile>%o<InnerBallistikProjectile>b                           XmlUserFileImport                           XmlUserFileDumpPropellant                           XmlUserFileDumpCaliber                          XmlUserFileDumpProjectile                           XmlUserFileDumpGun                          \tmp\20211008\innereBallistik              (           (e:\projekte\innereBa
```

### xml_import_projectile
- needle: `XmlUserFileImportProjectile`
- present: `True`
- index: `25498670`
```text
SqlDumpTable                            SqlDump                             ConvertToMySQL                          XmlUserFileDump                             XmlUserFileImportPropellant                             XmlUserFileImportProjectile                             XmlUserFileImportCaliber                            SaveCaliber                             %i4%o<InnerBallistikCaliber>b                           SaveProjectile
```

### xml_import_propellant
- needle: `XmlUserFileImportPropellant`
- present: `True`
- index: `25498614`
```text
%o<InnerBallistikProjectile>%s                          SqlDumpTable                            SqlDump                             ConvertToMySQL                          XmlUserFileDump                             XmlUserFileImportPropellant                             XmlUserFileImportProjectile                             XmlUserFileImportCaliber                            SaveCaliber                             %i4%o<InnerBalli
```

### xml_import_caliber
- needle: `XmlUserFileImportCaliber`
- present: `True`
- index: `25498726`
```text
ConvertToMySQL                          XmlUserFileDump                             XmlUserFileImportPropellant                             XmlUserFileImportProjectile                             XmlUserFileImportCaliber                            SaveCaliber                             %i4%o<InnerBallistikCaliber>b                           SaveProjectile                          %i4%o<InnerBallistikProjectile>b
```

### attach_database
- needle: `REALSQLDatabase.AttachDatabase`
- present: `True`
- index: `26569102`
```text
REALSQLDatabase.CreateDatabaseFile() as Boolean                $           $REALSQLDatabase.LastRowID() as Int64               6           6REALSQLDatabase.DetachDatabase(databaseName as String)             U           UREALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String) as Boolean              n           nREALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String) as Boole
```

### attach_database_with_key
- needle: `REALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String)`
- present: `True`
- index: `26569214`
```text
6           6REALSQLDatabase.DetachDatabase(databaseName as String)             U           UREALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String) as Boolean              n           nREALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String) as Boolean             0           0REALSQLDatabase.Encrypt(encryptionKey as String)                            REALSQLD
```

### encrypt
- needle: `REALSQLDatabase.Encrypt(encryptionKey as String)`
- present: `True`
- index: `26569350`
```text
se(file as FolderItem, databaseName as String) as Boolean              n           nREALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String) as Boolean             0           0REALSQLDatabase.Encrypt(encryptionKey as String)                            REALSQLDatabase.Decrypt                d           dREALSQLDatabase.SQLSelect(SelectString As String, fastForwardCursor as Boolean = false) as R
```

### decrypt
- needle: `REALSQLDatabase.Decrypt`
- present: `True`
- index: `26569426`
```text
nREALSQLDatabase.AttachDatabase(file as FolderItem, databaseName as String, encryptionKey as String) as Boolean             0           0REALSQLDatabase.Encrypt(encryptionKey as String)                            REALSQLDatabase.Decrypt                d           dREALSQLDatabase.SQLSelect(SelectString As String, fastForwardCursor as Boolean = false) as RecordSet               H           HREALSQLDatabase.Prepare(statement As Str
```

### cip_url
- needle: `https://bobp.cip-bobp.org`
- present: `True`
- index: `25538674`
```text
vii                             viii                            ix                          xii                             /uploads/tdcc/tab-{id}/{file}                           {id}                            https://bobp.cip-bobp.org                           InnerBallistikCaliberGroup                          AddEntry                            %o<InnerBallistikCaliber>%i4                            RemoveEntry
```

### cip_url_builder
- needle: `/uploads/tdcc/tab-{id}/{file}`
- present: `True`
- index: `25538586`
```text
iii                             iv                          vi                          vii                             viii                            ix                          xii                             /uploads/tdcc/tab-{id}/{file}                           {id}                            https://bobp.cip-bobp.org                           InnerBallistikCaliberGroup                          AddEntry
```

### saami_token
- needle: ` SAAMI `
- present: `True`
- index: `25508346`
```text
NOT NULL,  geloescht       INTEGER NOT NULL);                          9                           a                           z                           m                            CIP                             SAAMI                 	           	 Wildcat                            __                          %_                          _%             
           
<var name=                           value=
```

### wildcat_token
- needle: ` Wildcat `
- present: `True`
- index: `25508382`
```text
NOT NULL);                          9                           a                           z                           m                            CIP                             SAAMI                 	           	 Wildcat                            __                          %_                          _%             
           
<var name=                           value=                             \u
```

### projectilefile_tag
- needle: `<projectilefile>`
- present: `True`
- index: `25559752`
```text
)=round(                          ,4)                             0.000                           .000                            smax:                           `                                                         <projectilefile>                              <var name=                            </projectilefile>                             projectilefile                          can't find node <projectilefile>
```

### propellantfile_tag
- needle: `<propellantfile>`
- present: `True`
- index: `25565954`
```text
='                          status='                            origin='                            descr='                             imageUuid='                             imageDetailUuid='                           <propellantfile>                            imagedetailfile                             </propellantfile>                           propellantfile                          can't find node <propellantfile>
```

### caliberfile_tag
- needle: `<caliberfile>`
- present: `True`
- index: `25538006`
```text
_M                          shot_b                          shot_d                          shot_g                          shot_h                          shot_l                          shot_t                        <caliberfile>                           header             	           	cartridge                           footer                          </caliberfile>                          can't find node <caliberfile>
```

### get_datasheet_url
- needle: `GetDatasheetURL`
- present: `True`
- index: `25536398`
```text
ProjectileCaliber                           %o<UniversalJSONItem>%bb                          computeVolume                           computeS                            R1beta                          GetDatasheetURL                             %b%&s&s                             MaxLengthChamber                            MaxDiameterChamber                          N                           FLauf
```

### get_cip_url
- needle: `GetCIPURL`
- present: `True`
- index: `25537174`
```text
t_Header                            DictionarySet_Footer                            DictionarySet_Cartridge                             DictionarySet_Chamber                           IsValid                	           	GetCIPURL                           Sebert                          emin                            FG                          L3G                             ='                          select * from caliber where
```

### commandline_token
- needle: `CommandLine`
- present: `True`
- index: `27583`
```text
LoadResource    SetDllDirectoryW    LoadLibraryW    GetModuleFileNameW    MultiByteToWideChar   GetProcAddress    LoadLibraryA    LockResource  KERNEL32.dll    MessageBoxA USER32.dll    GetLastError    HeapFree  o GetCommandLineA   HeapSetInformation  : GetStartupInfoW - TerminateProcess    GetCurrentProcess > UnhandledExceptionFilter    SetUnhandledExceptionFilter   IsDebuggerPresent   HeapCreate    EncodePointer   DecodePointer   H
```

### shell_execute
- needle: `Shell.Execute`
- present: `True`
- index: `26577606`
```text
s Integer) as String               A           ARegExMatch.SubExpressionStartB(MatchNumber as Integer) as Integer                           Shell.__init                            Shell.__exit                            Shell.Execute(command as String)               6           6Shell.Execute(command as String, parameters as String)                          Shell.ReadAll() as String                           Shell.Write(s as String)
```

### grtdb_dev_path
- needle: `e:\projekte\innereBallistik\Tools\grtdb-`
- present: `True`
- index: `25501070`
```text
XmlUserFileDumpCaliber                          XmlUserFileDumpProjectile                           XmlUserFileDumpGun                          \tmp\20211008\innereBallistik              (           (e:\projekte\innereBallistik\Tools\grtdb-                            .db                3           3e:\projekte\innereBallistik\GordonsReloadingTool.db                               create table "status" (  id        IN
```
