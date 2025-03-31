import clr
import sys

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import Application, Form, Label, Button, DialogResult
from System.Drawing import Point

class ClientPopup(Form):
    def __init__(self, server_ip, server_port, server_name, server_uuid):
        Form.__init__(self)
        self.Text = f"Allow Read/Write Access for {server_name}"
        self.Width = 400
        self.Height = 250
        self.user_approved = None  # Boolean flag to store result

        label1 = Label()
        label1.Text = f"Server IP: {server_ip}\nServer Port: {server_port}\nServer Name: {server_name}\nServer UUID: {server_uuid}"
        label1.AutoSize = True
        label1.Location = Point(20, 20)

        label2 = Label()
        label2.Text = "Do you want to allow read/write access?"
        label2.AutoSize = True
        label2.Location = Point(20, 100)

        approveButton = Button()
        approveButton.Text = "Approve"
        approveButton.Location = Point(50, 150)
        approveButton.Click += self.on_approve

        denyButton = Button()
        denyButton.Text = "Deny"
        denyButton.Location = Point(200, 150)
        denyButton.Click += self.on_deny

        self.Controls.Add(label1)
        self.Controls.Add(label2)
        self.Controls.Add(approveButton)
        self.Controls.Add(denyButton)

    def on_approve(self, sender, event):
        self.user_approved = True
        self.DialogResult = DialogResult.OK  # Closes the dialog

    def on_deny(self, sender, event):
        self.user_approved = False
        self.DialogResult = DialogResult.Cancel  # Closes the dialog

def prompt_user(server_ip, server_port, server_name, server_uuid):
    Application.EnableVisualStyles()
    form = ClientPopup(server_ip, server_port, server_name, server_uuid)
    result = form.ShowDialog()  # Blocks until user chooses
    return form.user_approved

# === Usage Example ===
if __name__ == "__main__":
    approved = prompt_user("127.0.0.1", "5001", "DTPWA", "server_uuid")
    print(f"User approved: {approved}")

