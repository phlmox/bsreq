# Browse Saved Requests - bsReq

**Browse Saved Requests** is a Burp Suite extension developed in Jython that enables users to browse through their saved items.

![2](https://github.com/user-attachments/assets/74bf7658-a2f5-4326-bd97-d66360771635)

## Installation

1. **Download the Extension**

   Clone or download this repository to your local machine

2. **Configure Jython in Burp Suite**

   - Open Burp Suite.
   - Navigate to the **Extender** tab.
   - Go to the **Options** sub-tab.
   - Under **Python Environment**, click on **Select file**.
   - Browse to the location where you saved the Jython standalone JAR file and select it.
   - Click **OK** to confirm.

3. **Load the Extension**

   - Still under the **Extender** tab, go to the **Extensions** sub-tab.
   - Click on **Add**.
   - In the **Add Extension** dialog:
     - Set the **Extension type** to **Python**.
     - Click on **Select file** and browse to the `CustomTab.py` file from this repository.
   - Click **Next**, then **Finish** to load the extension.

