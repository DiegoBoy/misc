"""Burp editor extension example.

It creates a new tab in the proxy tab for some requests and responses, defined
by your criteria. In this tab, you define which text you want displayed. In the
repeater tab, you may edit that text, and the request will be rebuilt according
to your logic.

This design allows to minimize the amount of Python code interacting with Burp,
which runs the extension with Jython, and is slow to load, unload and debug.
By abstracting the interesting logic (present and edit requests) in a separate
Python module with no Burp dependency, you can add your own tests and develop
your extension faster.

Note Jython does not handle exceptions inside callbacks so try/except will not
work. Exceptions will be propagated to Java which then shows a Java stack trace
with no Python information, so you do not know where it was raised. Develop
your module so that there are no exceptions by checking for errors before.

Another interesting fact: calls from Python to Java are slow, so by putting
the parsing logic in a separate library rather than using some of the helpers
methods exposed by burp, it is noticeably faster.
"""

from burp import IBurpExtender
from burp import IMessageEditorTabFactory
from burp import IMessageEditorTab

# You may change the library here but keep it imported as editor.
import b64 as editor


class BurpExtender(IBurpExtender, IMessageEditorTabFactory):

  def registerExtenderCallbacks(self, callbacks):
    self._callbacks = callbacks
    callbacks.setExtensionName(editor.NAME)
    callbacks.registerMessageEditorTabFactory(self)
  
  def createNewInstance(self, controller, editable):
    return EditorTab(self, controller, editable)


class EditorTab(IMessageEditorTab):

  def __init__(self, extender, controller, editable):
    self._content = ''
    self._isRequest = False
    self._txtInput = extender._callbacks.createTextEditor()
    self._txtInput.setEditable(editable)
    
  def getTabCaption(self):
    return editor.TITLE
    
  def getUiComponent(self):
    return self._txtInput.getComponent()
    
  def isEnabled(self, content, isRequest):
    s = content.tostring()
    r = editor.Request.Parse(s) if isRequest else editor.Response.Parse(s)
    return r.Enabled() if r else False
    
  def setMessage(self, content, isRequest):
    if not content:
      self._txtInput.setText(None)
      return
    self._content = content
    self._isRequest = isRequest
    s = content.tostring()
    r = editor.Request.Parse(s) if isRequest else editor.Response.Parse(s)
    if not r:
      return
    self._txtInput.setText(r.Text())

  def getMessage(self):
    if not self._txtInput.isTextModified():
      return self._content
    assert self._isRequest
    r = editor.Request.Parse(self._content.tostring())
    if not r:
      return self._content
    r.Load(self._txtInput.getText().tostring())
    return r.String()
    
  def isModified(self):
    return self._txtInput.isTextModified()
    
  def getSelectedData(self):
    return self._txtInput.getSelectedText()
