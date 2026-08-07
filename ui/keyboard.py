from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QLineEdit, QComboBox, QAbstractSpinBox, QDateEdit, QPushButton, QPlainTextEdit, QTextEdit


def parse_number(text):
    s = str(text or '').strip().replace('$', '').replace(' ', '')
    if not s:
        return None
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        tail = s.rsplit(',', 1)[1]
        s = s.replace('.', '')
        s = s.replace(',', '.') if len(tail) <= 2 else s.replace(',', '')
    elif s.count('.') > 1:
        s = s.replace('.', '')
    elif '.' in s:
        left, right = s.rsplit('.', 1)
        if len(right) == 3 and left.isdigit():
            s = s.replace('.', '')
    try:
        return float(s)
    except ValueError:
        return None


def format_number(text, decimals=0):
    raw = str(text or '').strip()
    if not raw:
        return ''
    value = parse_number(raw)
    if value is None:
        return raw
    if decimals:
        return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'{round(value):,}'.replace(',', '.')


class KeyboardAndNumberFilter(QObject):
    """Navegación global y segura con Enter para los formularios del POS.

    Regla:
      * Click/foco en un campo editable -> contenido seleccionado.
      * Enter -> confirma la edición y va al siguiente campo del orden de foco.
      * Si no hay siguiente campo -> ejecuta keyboard_submit() o el botón de acción.
      * El Enter siempre se consume cuando viene de un editor para impedir que
        Qt active accidentalmente el botón por defecto y cierre el formulario.
      * Nunca se hace wrap-around al primer campo.
    """
    EDITABLE = (QLineEdit, QComboBox, QDateEdit, QAbstractSpinBox, QPlainTextEdit, QTextEdit)

    def eventFilter(self, obj, event):
        target = self._normalize_editor(obj)

        if event.type() == QEvent.FocusIn:
            self._select_editor(target)
            return False

        if event.type() == QEvent.FocusOut:
            if isinstance(target, QLineEdit) and target.property('numeric_format'):
                self._format_edit(target)
            elif isinstance(target, QAbstractSpinBox) and target.property('numeric_format'):
                self._format_spinbox(target)
            return False

        if event.type() != QEvent.KeyPress:
            return False
        print(
            "TECLA EN:",
            type(target).__name__,
            "EDITABLE:",
            self._is_editable(target)
        )

        if not self._is_editable(target) or target.property('keyboard_navigation_skip'):
            return False

        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            print("ENTER RECIBIDO EN:", type(target).__name__)
            # Completers/listas abiertas conservan Enter para seleccionar el resultado.
            if isinstance(target, QLineEdit) and target.completer() and target.completer().popup().isVisible():
                return False

            # Un campo multilínea puede pedir explícitamente que Enter inserte salto.
            if target.property('keyboard_enter_newline'):
                return False

            if isinstance(target, QLineEdit) and target.property('numeric_format'):
                self._format_edit(target)
            elif isinstance(target, QAbstractSpinBox) and target.property('numeric_format'):
                self._format_spinbox(target)

            self._advance_or_submit(target)
            # Fundamental: no dejar que Qt procese el Enter otra vez. Así nunca
            # activa el botón por defecto ni cierra el diálogo antes de confirmar.
            event.accept()
            return True

        if key == Qt.Key_Down:
            if self._advance(target, 1):
                event.accept()
                return True
        elif key == Qt.Key_Up:
            if self._advance(target, -1):
                event.accept()
                return True
        return False

    def _normalize_editor(self, obj):
        """Devuelve el control lógico cuando Qt entrega la tecla al editor interno."""
        if isinstance(obj, QAbstractSpinBox):
            return obj
        if isinstance(obj, QLineEdit):
            parent = obj.parentWidget()
            while parent is not None:
                if isinstance(parent, QAbstractSpinBox):
                    return parent
                parent = parent.parentWidget()
        return obj

    def _is_editable(self, w):
        return (isinstance(w, self.EDITABLE) and w.isEnabled() and w.isVisible()
                and not w.property('keyboard_navigation_skip'))

    def _select_editor(self, widget):
        if not self._is_editable(widget):
            return
        if isinstance(widget, QLineEdit):
            widget.selectAll()
        elif isinstance(widget, QAbstractSpinBox):
            try:
                le = widget.lineEdit()
                if le:
                    le.selectAll()
            except Exception:
                pass
        elif isinstance(widget, QComboBox):
            try:
                if widget.isEditable() and widget.lineEdit():
                    widget.lineEdit().selectAll()
            except Exception:
                pass
        elif isinstance(widget, (QPlainTextEdit, QTextEdit)):
            widget.selectAll()

    def _next_editable(self, widget, direction=1):
        """Recorre la cadena de foco real, ignorando editores internos.

        QDoubleSpinBox/QSpinBox contienen un QLineEdit interno. Ese editor
        también aparece en la cadena de foco y, si se lo toma como un campo
        independiente, Enter puede quedarse en el mismo control en vez de
        avanzar al siguiente. Aquí se salta cualquier elemento cuyo control
        lógico sea el mismo que el origen.
        """
        origin = self._normalize_editor(widget)
        current = origin
        visited = set()
        for _ in range(2000):
            current = (current.nextInFocusChain() if direction > 0
                       else current.previousInFocusChain())
            if current is None:
                return None
            # QFocusChain es circular. Si volvimos al control de origen,
            # llegamos al final real del formulario: NO hacer wrap al primer
            # campo. El siguiente Enter debe confirmar/guardar la acción.
            if current is origin:
                return None
            logical_current = self._normalize_editor(current)
            # Un QDoubleSpinBox/QSpinBox tiene un QLineEdit interno en la
            # cadena de foco. No es un campo nuevo: hay que saltarlo y seguir
            # buscando el siguiente control real.
            if logical_current is origin:
                continue
            ident = id(current)
            if ident in visited:
                return None
            visited.add(ident)

            logical = logical_current
            if self._is_editable(logical):
                return logical
        return None

    def _advance(self, widget, direction=1):
        nxt = self._next_editable(widget, direction)
        if nxt is None:
            return False
        nxt.setFocus(Qt.TabFocusReason)
        self._select_editor(nxt)
        return True

    def _advance_or_submit(self, widget):

        window = widget.window()

        sequence = None


        # Buscar desde el widget real hacia arriba
        # hasta encontrar cualquier contenedor con la secuencia ENTER

        current = widget

        while current is not None:

            sequence = getattr(
                current,
                '_keyboard_enter_sequence',
                None
            )

            if sequence:

                window = current
                break


            current = current.parentWidget()



        print(
            "VENTANA:",
            type(window).__name__
        )

        print(
            "SEQUENCE:",
            sequence
        )

        print(
            "WIDGET:",
            widget.objectName(),
            type(widget).__name__
        )


        print(
            "VENTANA:",
            type(window).__name__
        )

        print(
            "SEQUENCE:",
            sequence
        )

        print(
            "WIDGET:",
            widget.objectName(),
            type(widget).__name__
        )



        if sequence:

            try:

                logical = self._normalize_editor(
                    widget
                )

                seq = [
                    w
                    for w in sequence
                    if self._is_editable(w)
                ]


                for i, current in enumerate(seq):

                    if current == logical:


                        if i + 1 < len(seq):

                            nxt = seq[i + 1]

                            nxt.setFocus(
                                Qt.TabFocusReason
                            )

                            self._select_editor(
                                nxt
                            )

                            return True



                        return self._submit_form(
                            window
                        )


            except Exception as e:

                print(
                    "ERROR SECUENCIA ENTER:",
                    e
                )



        # Si el formulario marca explícitamente último campo

        if widget.property(
            'keyboard_last'
        ):

            return self._submit_form(
                window
            )



        # Navegación normal

        if self._advance(
            widget,
            1
        ):

            return True



        # Último campo

        return self._submit_form(
            window
        )
    def _submit_form(self, window):
        method = getattr(window, 'keyboard_submit', None)
        if callable(method):
            try:
                result = method()
                return True if result is None else bool(result)
            except Exception:
                # No permitir que una excepción devuelva Enter a Qt y active
                # accidentalmente el botón por defecto.
                return True

        buttons = window.findChildren(QPushButton)
        # Elegimos la acción principal por prioridad, no por el orden en que
        # los botones fueron creados. Así Enter en el último campo no termina
        # presionando accidentalmente "Agregar", "Cerrar" o "Cancelar".
        priorities = (
            ('guardar', 100), ('confirmar', 95), ('cobrar', 95),
            ('finalizar', 90), ('aplicar', 85), ('aceptar', 80),
            ('actualizar', 75), ('crear', 70), ('continuar', 65),
            ('añadir', 40), ('agregar', 35),
        )
        candidates = []
        for btn in buttons:
            if not (btn.isEnabled() and btn.isVisible()):
                continue
            txt = (btn.text() or '').lower().strip()
            if txt in ('cancelar', 'cerrar', 'salir'):
                continue
            score = 0
            for word, value in priorities:
                if txt == word:
                    score = max(score, value + 10)
                elif word in txt:
                    score = max(score, value)
            if btn.property('keyboard_primary'):
                score = 1000
            if score:
                candidates.append((score, btn))
        if candidates:
            candidates.sort(key=lambda pair: pair[0], reverse=True)
            candidates[0][1].click()
            return True
        return True

    def _format_spinbox(self, spin):
        try:
            value = spin.value()
            spin.setValue(value)
        except Exception:
            pass

    def _format_edit(self, edit):
        if edit.property('_formatting'):
            return
        text = edit.text()
        formatted = format_number(text, int(edit.property('numeric_decimals') or 0))
        if formatted == text:
            return
        edit.setProperty('_formatting', True)
        try:
            edit.setText(formatted)
            edit.setCursorPosition(len(formatted))
        finally:
            edit.setProperty('_formatting', False)


def setup_numeric(widget, decimals=0):
    widget.setProperty('numeric_format', True)
    widget.setProperty('numeric_decimals', decimals)
    return widget


def setup_keyboard_exceptions(*widgets):
    for widget in widgets:
        widget.setProperty('keyboard_navigation_skip', True)
