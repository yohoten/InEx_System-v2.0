; ── Inno Setup 安装脚本 ─────────────────────────────────
; 由 build.py --installer 自动生成
; 生成时间: 2026-05-17 14:24:16
; 需要 Inno Setup 6+: https://jrsoftware.org/isinfo.php
; ─────────────────────────────────────────────────────────

#define MyAppName "InEx System"
#define MyAppVersion "2.0"
#define MyAppPublisher "InEx System Team"
#define MyAppURL "https://github.com/yohoten/InEx_System"
#define MyAppExeName "InEx_System_v2.0.exe"
#define MyAppId "InExSystem.InEx_System.v2.0"
#define MyAppDescription "个人收支管理系统"

[Setup]
AppId={{{#MyAppId}}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=InEx_System_v2.0_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=InEx_System.ico
UninstallDisplayIcon={app}\InEx_System_v2.0.exe
PrivilegesRequiredOverridesAllowed=commandline dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 注意: 请将下方 Source 路径改为实际的打包输出目录
Source: "dist\InEx_System_v2.0\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\InEx System"; Filename: "{app}\InEx_System_v2.0.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 InEx System"; Filename: "{uninstallexe}"
Name: "{autodesktop}\InEx System"; Filename: "{app}\InEx_System_v2.0.exe"; Tasks: desktopicon; WorkingDir: "{app}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\InEx System"; Filename: "{app}\InEx_System_v2.0.exe"; Tasks: quicklaunchicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\InEx_System_v2.0.exe"; Description: "启动 InEx System"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 首次安装提示
  end;
end;
