; packaging/installer.iss — Kast 2.0 Windows Studio Edition Inno Setup Scripti
#define MyAppName "Kast Studio"
#ifndef MyAppVersion
#define MyAppVersion "2.1.1"
#endif
#define MyAppPublisher "Umut Aktepe"
#define MyAppURL "https://github.com/umutaktepe/Kast"
#define MyAppExeName "KastStudio.exe"

[Setup]
AppId={{D37E6F90-7F89-4A73-98C3-2A676E4B15C0}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Kast-v{#MyAppVersion}-Setup
SetupIconFile=assets\kast.ico
UninstallDisplayIcon={app}\assets\kast.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; PyInstaller ile derlenen tüm klasör
Source: "..\dist\KastStudio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "assets\kast.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\kast.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\kast.ico"; Tasks: desktopicon
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// --- Word ve LibreOffice Varlık Denetimi ve Sessiz Kurulum ---

function IsWordInstalled(): Boolean;
var
  AppPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Winword.exe', '', AppPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Winword.exe', '', AppPath) or
            RegKeyExists(HKCR, 'Word.Application');
end;

function IsLibreOfficeInstalled(): Boolean;
var
  InstallPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\LibreOffice\UNO\InstallPath', '', InstallPath) or
            RegQueryStringValue(HKCU, 'SOFTWARE\LibreOffice\UNO\InstallPath', '', InstallPath) or
            RegKeyExists(HKLM, 'SOFTWARE\The Document Foundation\LibreOffice') or
            RegKeyExists(HKCU, 'SOFTWARE\The Document Foundation\LibreOffice') or
            FileExists(ExpandConstant('{pf}\LibreOffice\program\soffice.exe')) or
            FileExists(ExpandConstant('{pf32}\LibreOffice\program\soffice.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\LibreOffice\program\soffice.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  WingetCmd: String;
  PSCmd: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Eğer ne Word ne de LibreOffice varsa kullanıcıya hiç hissettirmeden arka planda LibreOffice kur
    if (not IsWordInstalled()) and (not IsLibreOfficeInstalled()) then
    begin
      WizardForm.StatusLabel.Caption := 'Döküman sayfa doğrulaması için gerekli bileşenler hazırlanıyor (LibreOffice)...';
      
      // 1. Önce winget ile sessiz kurulum dene
      WingetCmd := '/c winget install --id TheDocumentFoundation.LibreOffice -e --silent --accept-package-agreements --accept-source-agreements';
      if not Exec('cmd.exe', WingetCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      begin
        // 2. Winget başarısız olursa PowerShell ile doğrudan MSI indir ve sessiz kur
        PSCmd := '-ExecutionPolicy Bypass -Command "' +
                 '$url = ''https://download.documentfoundation.org/libreoffice/stable/latest/win/x86_64/LibreOffice_latest_Win_x86-64.msi''; ' +
                 '$dest = Join-Path $env:TEMP ''LibreOfficeInstall.msi''; ' +
                 'try { ' +
                 '  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ' +
                 '  Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing; ' +
                 '  Start-Process msiexec.exe -ArgumentList ''/i'', $dest, ''/qn'', ''/norestart'' -Wait; ' +
                 '  Remove-Item $dest -Force -ErrorAction SilentlyContinue; ' +
                 '} catch {}"';
        Exec('powershell.exe', PSCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;
