If WScript.Arguments.Count < 2 Then
    WScript.Echo "Usage: cscript CreateShortcut.vbs <TargetPath> <ShortcutName>"
    WScript.Quit 1
End If

Dim WshShell, ShortcutPath, TargetPath, ShortcutName, WorkingDir

Set WshShell = WScript.CreateObject("WScript.Shell")

TargetPath = WScript.Arguments(0)
ShortcutName = WScript.Arguments(1)

ShortcutPath = WshShell.SpecialFolders("Desktop") & "\" & ShortcutName

Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")
WorkingDir = fso.GetParentFolderName(TargetPath)

Set Shortcut = WshShell.CreateShortcut(ShortcutPath)
Shortcut.TargetPath = TargetPath
Shortcut.WorkingDirectory = WorkingDir
Shortcut.WindowStyle = 1
Shortcut.Save
