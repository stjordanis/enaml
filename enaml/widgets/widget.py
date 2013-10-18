#------------------------------------------------------------------------------
# Copyright (c) 2013, Nucleic Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#------------------------------------------------------------------------------
from atom.api import (
    Bool, Enum, Unicode, Coerced, Str, Typed, ForwardTyped, observe
)

from enaml.application import Application
from enaml.colors import ColorMember
from enaml.core.declarative import d_
from enaml.fonts import FontMember
from enaml.layout.geometry import Size

from .styling import Style, StyleSheet
from .toolkit_object import ToolkitObject, ProxyToolkitObject


class ProxyWidget(ProxyToolkitObject):
    """ The abstract definition of a proxy Widget object.

    """
    #: A reference to the Widget declaration.
    declaration = ForwardTyped(lambda: Widget)

    def set_enabled(self, enabled):
        raise NotImplementedError

    def set_visible(self, visible):
        raise NotImplementedError

    def set_background(self, background):
        raise NotImplementedError

    def set_foreground(self, foreground):
        raise NotImplementedError

    def set_font(self, font):
        raise NotImplementedError

    def set_minimum_size(self, minimum_size):
        raise NotImplementedError

    def set_maximum_size(self, maximum_size):
        raise NotImplementedError

    def set_tool_tip(self, tool_tip):
        raise NotImplementedError

    def set_status_tip(self, status_tip):
        raise NotImplementedError

    def set_show_focus_rect(self, show_focus_rect):
        raise NotImplementedError

    def ensure_visible(self):
        raise NotImplementedError

    def ensure_hidden(self):
        raise NotImplementedError

    def restyle(self, styles):
        raise NotImplementedError


class Widget(ToolkitObject):
    """ The base class of visible widgets in Enaml.

    """
    #: Whether or not the widget is enabled.
    enabled = d_(Bool(True))

    #: Whether or not the widget is visible.
    visible = d_(Bool(True))

    #: The style class to which this widget belongs. An empty string
    #: indicates the widget does not belong to any style class.
    styleclass = d_(Str())

    #: The background color of the widget.
    background = d_(ColorMember())

    #: The foreground color of the widget.
    foreground = d_(ColorMember())

    #: The font used for the widget.
    font = d_(FontMember())

    #: The minimum size for the widget. The default means that the
    #: client should determine an intelligent minimum size.
    minimum_size = d_(Coerced(Size, (-1, -1)))

    #: The maximum size for the widget. The default means that the
    #: client should determine an intelligent maximum size.
    maximum_size = d_(Coerced(Size, (-1, -1)))

    #: The tool tip to show when the user hovers over the widget.
    tool_tip = d_(Unicode())

    #: The status tip to show when the user hovers over the widget.
    status_tip = d_(Unicode())

    #: A flag indicating whether or not to show the focus rectangle for
    #: the given widget. This is not necessarily support by all widgets
    #: on all clients. A value of None indicates to use the default as
    #: supplied by the client.
    show_focus_rect = d_(Enum(None, True, False))

    #: A reference to the ProxyWidget object.
    proxy = Typed(ProxyWidget)

    #--------------------------------------------------------------------------
    # Observers
    #--------------------------------------------------------------------------
    @observe('enabled', 'visible', 'background', 'foreground', 'font',
        'minimum_size', 'maximum_size', 'show_focus_rect', 'tool_tip',
        'status_tip')
    def _update_proxy(self, change):
        """ Update the proxy widget when the Widget data changes.

        This method only updates the proxy when an attribute is updated;
        not when it is created or deleted.

        """
        # The superclass implementation is sufficient.
        super(Widget, self)._update_proxy(change)

    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
    def show(self):
        """ Ensure the widget is shown.

        Calling this method will also set the widget visibility to True.

        """
        self.visible = True
        if self.proxy_is_active:
            self.proxy.ensure_visible()

    def hide(self):
        """ Ensure the widget is hidden.

        Calling this method will also set the widget visibility to False.

        """
        self.visible = False
        if self.proxy_is_active:
            self.proxy.ensure_hidden()

    def get_style(self):
        """ Get the style defined on the item.

        Returns
        -------
        result : Style or None
            The last Style child defined on the widget, or None if the
            widget has no such child.

        """
        for child in reversed(self.children):
            if isinstance(child, Style):
                return child

    def get_stylesheet(self):
        """ Get the style sheet defined on the item.

        Returns
        -------
        result : StyleSheet or None
            The last StyleSheet child defined on the widget, or None if
            the widget has no such child.

        """
        for child in reversed(self.children):
            if isinstance(child, StyleSheet):
                return child

    def restyle(self):
        """ Restyle the widget hierarchy starting with this widget.

        This method is called automatically by the framework at the
        appropriate times. It will not typically need to be called
        directly by user code.

        """
        self._restyle()

    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
    def _restyle(self, ancestors=None):
        """ The restyle implementation method.

        Parameters
        ----------
        ancestors : list or None
            The list of ancestor style sheets. If this is None, the
            ancestor hierarchy will be traversed to collect the style
            sheets.

        """
        if not self.proxy_is_active:
            return

        if ancestors is None:
            sheets = self._get_ancestor_stylesheets()
        else:
            sheets = ancestors[:]

        this_sheet = self.get_stylesheet()
        if this_sheet is not None:
            sheets.append(this_sheet)

        # Style the children bottom-up.
        for child in self.children:
            if isinstance(child, Widget):
                child._restyle(sheets)

        these_styles = []
        for sheet in sheets:
            matches = []
            for style in sheet.styles():
                specificity = style.match(self)
                if specificity > 0:
                    matches.append((specificity, style))
            if matches:
                matches.sort()
                these_styles.extend(style for _, style in matches)

        this_style = self.get_style()
        if this_style is not None:
            these_styles.append(this_style)

        self.proxy.restyle(these_styles)

    def _get_ancestor_stylesheets(self):
        """ Get a list of ancestor stylesheets.

        Returns
        -------
        result : list
            A list of stylesheet objects for the ancestors of this
            widget, in order of increasing precedence.

        """
        sheets = []
        for w in self.traverse_ancestors():
            if isinstance(w, Widget):
                sheet = w.get_stylesheet()
                if sheet is not None:
                    sheets.append(w)
        app = Application.instance()
        if app is not None and app.stylesheet is not None:
            sheets.append(app.stylesheet)
        if sheets:
            sheets.reverse()
        return sheets
