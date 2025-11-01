Sub FromGovToFormatted1()
'
' FromGovToFormatted Macro
'

'
'activate cell 1 column right of date cell and run this
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlToRight)).Select
    ActiveCell.Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlToRight)).Select
    Range(Selection, Selection.End(xlDown)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Range(Selection, Selection.End(xlToRight)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(0, 1).Range("A1").Select
    Range(Selection, Selection.End(xlDown)).Select
    Selection.Cut
    ActiveCell.Offset(0, 1).Range("A1").Select
    ActiveSheet.Paste
    ActiveCell.Offset(-1, -23).Range("A1").Select
End Sub


Sub FromGovToFormatted2()
'
'
'FromGovToFormatted2 Macro

'
'activate date cell just before the 1st date cell you just copied in and run this
Dim x As Integer: x = 12
For counter = 0 To x
    ActiveCell.Offset(0, 2).Range("A1").Select
    Selection.AutoFill Destination:=ActiveCell.Range("A1:A365")
Next counter
End Sub

Sub FromGovToFormatted3()
Sheets(1).Select
Range("A1").Select
On Error Resume Next
Set mylastcell = Cells(1, 1).SpecialCells(xlLastCell)
mylastcelladd = Cells(mylastcell.Row, mylastcell.Column).Address
myrange = "A2:" & mylastcelladd
Range(myrange).Select
Selection.HorizontalAlignment = xlLeft
Selection.VerticalAlignment = xlVAlignTop
End Sub


Sub FromGovToFormatted()
'activate cell 1 column right of date cell and run this
Call FromGovToFormatted1
Call FromGovToFormatted2
Call FromGovToFormatted3
End Sub


Sub SumIfAbove0()
'activate left-most column (where you want summation to go) and run this
Dim offsetY As Integer: offsetY = -22
Dim summm As Double: summ = 0

Do While offsetY < -1
If ActiveCell.Offset(0, offsetY).Value = 0 Then
Else
summm = summm + ActiveCell.Offset(0, offsetY).Value
End If
offsetY = offsetY + 2
Loop
ActiveCell.Value = summm
End Sub

Sub loopSumIfAbove0()

Dim totalRows As Integer: totalRows = InputBox("How many rows?")
Dim counter As Integer: counter = 0

Do While counter < totalRows
Call SumIfAbove0
ActiveCell.Offset(1, 0).Activate
counter = counter + 1
Loop
End Sub
Sub test0()
Debug.Print ("test0")
End Sub
