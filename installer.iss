; ---------------------------------------------------------------------------
; 1. APPLICATION METADATA & CONFIGURATION
; ---------------------------------------------------------------------------
[Setup]
AppName=BOINC Discord RPC
AppVersion=2.0
AppPublisher=Exottiiik
DefaultDirName={localappdata}\Programs\BOINC-RPC
DefaultGroupName=BOINC Discord RPC
OutputBaseFilename=BOINC-RPC-Windows-Installer
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\app_icon.ico

; ---------------------------------------------------------------------------
; 2. INTERNATIONALIZATION (LANGUAGES)
; ---------------------------------------------------------------------------
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[CustomMessages]
english.BoincPageTitle=BOINC Configuration
english.BoincPageDesc=Location of the RPC authentication file
english.BoincPageSub=Please confirm the location of BOINC's gui_rpc_auth.cfg file. Leave default if unmodified.
english.BoincPathLabel=File path:
english.GithubNote=Note: If you notice any bad translations, please report it on the BOINC Discord or submit a PR on GitHub: https://github.com/Exottiiik/BOINC-RPC

french.BoincPageTitle=Configuration de BOINC
french.BoincPageDesc=Localisation du fichier d'authentification RPC
french.BoincPageSub=Veuillez confirmer l'emplacement du fichier gui_rpc_auth.cfg de BOINC. Laissez par défaut si vous n'avez rien modifié.
french.BoincPathLabel=Chemin du fichier :
french.GithubNote=Note : Si vous remarquez de mauvaises traductions, n'hésitez pas à le signaler sur le Discord de BOINC ou à faire une PR sur GitHub : https://github.com/Exottiiik/BOINC-RPC

italian.BoincPageTitle=Configurazione di BOINC
italian.BoincPageDesc=Posizione del file di autenticazione RPC
italian.BoincPageSub=Conferma la posizione del file gui_rpc_auth.cfg di BOINC. Lascia i valori predefiniti se non modificati.
italian.BoincPathLabel=Percorso del file:
italian.GithubNote=Nota: Se riscontri traduzioni errate, segnalalo sul Discord di BOINC o fai una PR su GitHub: https://github.com/Exottiiik/BOINC-RPC

russian.BoincPageTitle=Конфигурация BOINC
russian.BoincPageDesc=Расположение файла аутентификации RPC
russian.BoincPageSub=Пожалуйста, подтвердите расположение файла gui_rpc_auth.cfg для BOINC. Оставьте по умолчанию, если он не изменен.
russian.BoincPathLabel=Путь к файлу:
russian.GithubNote=Примечание: Если вы заметили неточности в переводе, сообщите об этом в Discord BOINC или создайте PR на GitHub: https://github.com/Exottiiik/BOINC-RPC

chinese.BoincPageTitle=BOINC 配置
chinese.BoincPageDesc=RPC 认证文件的位置
chinese.BoincPageSub=请确认 BOINC 的 gui_rpc_auth.cfg 文件位置。如果未修改，请保持默认。
chinese.BoincPathLabel=文件路径:
chinese.GithubNote=注意：如果您发现翻译错误，请在 BOINC Discord 上报告或在 GitHub 上提交 PR：https://github.com/Exottiiik/BOINC-RPC

; ---------------------------------------------------------------------------
; 4. EMBEDDED FILES
; ---------------------------------------------------------------------------
[Files]
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\python_embed\*"; DestDir: "{app}\python_embed"; Excludes: "pythonw.exe"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build\python_embed\pythonw.exe"; DestDir: "{app}\python_embed"; DestName: "BOINC-Discord-RPC.exe"; Flags: ignoreversion
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

; ---------------------------------------------------------------------------
; 5. SHORTCUTS & ICONS
; ---------------------------------------------------------------------------
[Icons]
Name: "{userprograms}\BOINC Discord RPC"; Filename: "{app}\python_embed\BOINC-Discord-RPC.exe"; Parameters: """{app}\src\boinc_rpc_daemon.py"""; IconFilename: "{app}\app_icon.ico"
Name: "{userstartup}\BOINC Discord RPC"; Filename: "{app}\python_embed\BOINC-Discord-RPC.exe"; Parameters: """{app}\src\boinc_rpc_daemon.py"""; IconFilename: "{app}\app_icon.ico"

; ---------------------------------------------------------------------------
; 6. RUN AFTER INSTALLATION
; ---------------------------------------------------------------------------
[Run]
Filename: "schtasks"; Parameters: "/Create /F /TN ""BOINCDiscordRPC"" /TR ""'{app}\python_embed\BOINC-Discord-RPC.exe' '{app}\src\boinc_rpc_daemon.py'"" /SC ONLOGON"; Flags: runhidden
Filename: "{app}\python_embed\BOINC-Discord-RPC.exe"; Parameters: """{app}\src\boinc_rpc_daemon.py"""; Flags: nowait postinstall skipifsilent

; ---------------------------------------------------------------------------
; 7. CLEANUP DURING UNINSTALLATION
; ---------------------------------------------------------------------------
[UninstallRun]
RunOnceId: "StopDaemon"; Filename: "{cmd}"; Parameters: "/C taskkill /F /IM ""BOINC-Discord-RPC.exe"" /T"; Flags: runhidden waituntilterminated
RunOnceId: "DelSchTask"; Filename: "schtasks"; Parameters: "/Delete /TN ""BOINCDiscordRPC"" /F"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\*"
Type: dirifempty; Name: "{app}"

; ---------------------------------------------------------------------------
; 8. WIZARD LOGIC & .ENV GENERATION
; ---------------------------------------------------------------------------
[Code]
var
  BoincPathPage: TInputFileWizardPage;
  GithubLabel: TLabel;

procedure OpenGithubClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExec('open', 'https://github.com/Exottiiik/BOINC-RPC', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

procedure InitializeWizard;
var
  DefaultPath: String;
begin
  BoincPathPage := CreateInputFilePage(wpSelectDir,
    ExpandConstant('{cm:BoincPageTitle}'),
    ExpandConstant('{cm:BoincPageDesc}'),
    ExpandConstant('{cm:BoincPageSub}'));

  BoincPathPage.Add(ExpandConstant('{cm:BoincPathLabel}'), 
    'Configuration files (*.cfg)|*.cfg|All files (*.*)|*.*', 
    '.cfg');

  DefaultPath := 'C:\ProgramData\BOINC\gui_rpc_auth.cfg'; 
  BoincPathPage.Values[0] := DefaultPath;

  GithubLabel := TLabel.Create(WizardForm);
  GithubLabel.Parent := BoincPathPage.Surface;
  GithubLabel.Caption := ExpandConstant('{cm:GithubNote}');
  GithubLabel.Top := BoincPathPage.Surface.Height - 45;
  GithubLabel.Width := BoincPathPage.Surface.Width;
  GithubLabel.WordWrap := True;
  GithubLabel.Font.Style := [fsItalic, fsUnderline];
  GithubLabel.Font.Color := clBlue;
  GithubLabel.Cursor := crHand;
  GithubLabel.OnClick := @OpenGithubClick;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir, ConfigPath, JsonContent, EscapedPath: String;
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    Exec('taskkill.exe', '/F /IM "BOINC-Discord-RPC.exe" /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;

  if CurStep = ssPostInstall then
  begin
    ConfigDir := ExpandConstant('{%USERPROFILE}\.config\boinc-rpc');
    ConfigPath := ConfigDir + '\config.json';

    if not DirExists(ConfigDir) then
      ForceDirectories(ConfigDir);
    if not FileExists(ConfigPath) then
    begin
      EscapedPath := BoincPathPage.Values[0];
      StringChange(EscapedPath, '\', '\\');
      JsonContent := '{' + #13#10 +
                     '  "discord_client_id": "1509951042958266580",' + #13#10 +
                     '  "update_interval": 15,' + #13#10 +
                     '  "debug_mode": false,' + #13#10 +
                     '  "nodes": [' + #13#10 +
                     '    {' + #13#10 +
                     '      "name": "Localhost",' + #13#10 +
                     '      "host": "127.0.0.1",' + #13#10 +
                     '      "port": 31416,' + #13#10 +
                     '      "password_path": "' + EscapedPath + '",' + #13#10 +
                     '      "password": ""' + #13#10 +
                     '    }' + #13#10 +
                     '  ]' + #13#10 +
                     '}';
      SaveStringToFile(ConfigPath, JsonContent, False);
    end;
  end;
end;