from burp import IBurpExtender, ITab, IMessageEditorController, IProxyListener 
from javax.swing import JPanel, JSplitPane, JTable, JScrollPane, ListSelectionModel, JButton, JFileChooser, JLabel, JOptionPane
from javax.swing.event import ListSelectionListener
from javax.swing.table import DefaultTableModel
from java.awt import Dimension, FlowLayout, BorderLayout,Font, Color
from java.io import File
from xml.dom import minidom
import base64

class NonEditableTableModel(DefaultTableModel):
    def isCellEditable(self, row, col):
        return False

class BurpExtender(IBurpExtender, ITab, ListSelectionListener, IMessageEditorController, IProxyListener):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("Browse Saved Requests")
        self._main_panel = JPanel(BorderLayout())
        self._top_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        self._title = JLabel("Browse Saved Requests by @phlmox v1.0   ")
        self._title.setFont(Font("Tahoma", Font.BOLD, 14))
        self._title.setForeground(Color(214,48,49 ))
        self._top_panel.add(self._title)
        self._load_button = JButton("Load Requests", actionPerformed=self.load_requests)
        self._top_panel.add(self._load_button)
        self._table_model = self._create_table_model()
        self._table = JTable(self._table_model)
        self._table.getSelectionModel().addListSelectionListener(self)
        self._table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        self._table_scroll = JScrollPane(self._table)
        self._table_scroll.setPreferredSize(Dimension(800, 600))
        self._request_viewer = callbacks.createMessageEditor(self, False)
        self._response_viewer = callbacks.createMessageEditor(self, False)
        self._vertical_split = JSplitPane(
            JSplitPane.VERTICAL_SPLIT,
            self._request_viewer.getComponent(),
            self._response_viewer.getComponent()
        )
        self._vertical_split.setDividerLocation(0.5)
        self._vertical_split.setResizeWeight(0.5)
        self._vertical_split.setContinuousLayout(True)
        self._split_pane = JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT,
            self._table_scroll,
            self._vertical_split
        )
        self._split_pane.setDividerLocation(0.5)
        self._split_pane.setResizeWeight(0.5)
        self._split_pane.setContinuousLayout(True)
        self._main_panel.add(self._top_panel, BorderLayout.NORTH)
        self._main_panel.add(self._split_pane, BorderLayout.CENTER)
        self._http_data = []
        callbacks.registerProxyListener(self)
        callbacks.addSuiteTab(self)

    def getTabCaption(self):
        return "bsReq"

    def getUiComponent(self):
        return self._main_panel

    def _create_table_model(self):
        columns = ["URL", "Method", "Status", "Content Length", "Mimetype"]
        model = NonEditableTableModel(columns, 0)
        return model

    def load_requests(self, event):
        chooser = JFileChooser()
        chooser.setDialogTitle("Select XML File of Requests")
        chooser.setFileSelectionMode(JFileChooser.FILES_ONLY)
        chooser.setAcceptAllFileFilterUsed(False)

        result = chooser.showOpenDialog(None)
        if result == JFileChooser.APPROVE_OPTION:
            selected_file = chooser.getSelectedFile()
            if selected_file is not None:
                try:
                    self._parse_and_load_xml(selected_file)
                    JOptionPane.showMessageDialog(
                        self._main_panel, 
                        "Requests loaded successfully!", 
                        "Success", 
                        JOptionPane.INFORMATION_MESSAGE
                    )
                except Exception as e:
                    JOptionPane.showMessageDialog(
                        self._main_panel, 
                        "Failed to load requests!\n" + str(e),
                        "Error", 
                        JOptionPane.ERROR_MESSAGE
                    )
            else:
                JOptionPane.showMessageDialog(
                    self._main_panel, 
                    "No file selected.", 
                    "Warning", 
                    JOptionPane.WARNING_MESSAGE
                )

    def _parse_and_load_xml(self, file):
        try:
            file_path = file.getAbsolutePath()
            self._callbacks.printOutput("Parsing XML file: " + file_path)
            with open(file_path, "r") as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("The selected file is empty")
            dom_tree = minidom.parse(file_path)
            collection = dom_tree.getElementsByTagName("item")
            self._table_model.setRowCount(0)
            self._http_data = []

            for item in collection:
                print(item)
                if len(item.getElementsByTagName("url")[0].childNodes)==0: continue
                url = item.getElementsByTagName("url")[0].childNodes[0].data

                if len(item.getElementsByTagName("method")[0].childNodes)==0: continue
                method = item.getElementsByTagName("method")[0].childNodes[0].data

                if len(item.getElementsByTagName("status")[0].childNodes)==0: continue
                status = item.getElementsByTagName("status")[0].childNodes[0].data
                
                if len(item.getElementsByTagName("responselength")[0].childNodes)==0: continue
                responselength = item.getElementsByTagName("responselength")[0].childNodes[0].data
                
                mimetype = item.getElementsByTagName("mimetype")[0].childNodes
                mimetype = mimetype[0].data if len(mimetype)!=0 else "null" 
                
                request_elem = item.getElementsByTagName("request")[0]
                response_elem = item.getElementsByTagName("response")[0]
                

                request_base64 = request_elem.getAttribute("base64").lower() == 'true'
                response_base64 = response_elem.getAttribute("base64").lower() == 'true'

                request_data = request_elem.childNodes[0].data.strip()
                response_data = response_elem.childNodes[0].data.strip()
                if request_base64:
                    try:
                        request_bytes = base64.b64decode(request_data)
                    except Exception as e:
                        self._callbacks.printError("Failed to decode request: " + str(e))
                        request_bytes = request_data.encode('utf-8')
                else:
                    request_bytes = request_data.encode('utf-8')
                if response_base64:
                    try:
                        response_bytes = base64.b64decode(response_data)
                    except Exception as e:
                        self._callbacks.printError("Failed to decode response: " + str(e))
                        response_bytes = response_data.encode('utf-8')
                else:
                    response_bytes = response_data.encode('utf-8')
                self._http_data.append({
                    "url": url,
                    "method": method,
                    "status": status,
                    "content_length": responselength,
                    "mime_type": mimetype,
                    "request": request_bytes,
                    "response": response_bytes
                })
                self._table_model.addRow([
                    url,
                    method,
                    status,
                    responselength,
                    mimetype
                ])
        except Exception as e:
            self._callbacks.printError("Error parsing XML: " + str(e))
            JOptionPane.showMessageDialog(
                self._main_panel, 
                "Failed to load requests!\n" + str(e),
                "Error", 
                JOptionPane.ERROR_MESSAGE
            )

    def valueChanged(self, event):
        if not event.getValueIsAdjusting():
            selected_row = self._table.getSelectedRow()
            if selected_row != -1 and selected_row < len(self._http_data):
                data_entry = self._http_data[selected_row]
                http_request = data_entry["request"]
                http_response = data_entry["response"]
                self._request_viewer.setMessage(http_request, True)
                self._response_viewer.setMessage(http_response, False)
            else:
                self._request_viewer.setMessage(None, True)
                self._response_viewer.setMessage(None, False)

    def getHttpService(self):
        return None

    def getRequest(self):
        return None

    def getResponse(self):
        return None

    def processProxyMessage(self, messageIsRequest, messageInfo):
        if not messageIsRequest:
            http_service = messageInfo.getHttpService()
            url = self._helpers.analyzeRequest(messageInfo).getUrl().toString()
            method = self._helpers.analyzeRequest(messageInfo).getMethod()
            response = messageInfo.getResponse()
            analyze_response = self._helpers.analyzeResponse(response)
            status = analyze_response.getStatusCode()
            status_text = self._helpers.analyzeResponse(response).getStatusText()
            headers = analyze_response.getHeaders()
            content_length = "0"
            mimetype = "-"
            for header in headers:
                if header.lower().startswith("content-length"):
                    content_length = header.split(":")[1].strip()
                elif header.lower().startswith("content-type"):
                    mimetype = header.split(":")[1].strip().split(";")[0]
            entry = [url, method, status + " " + status_text, content_length, mimetype]
            self._http_data.append({
                "url": url,
                "method": method,
                "status": status + " " + status_text,
                "content_length": content_length,
                "mime_type": mimetype,
                "request": messageInfo.getRequest(),
                "response": response
            })
            self._table_model.addRow(entry)
