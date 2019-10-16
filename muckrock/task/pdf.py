# -*- coding: utf-8 -*-
"""
PDF Class for Snail Mail PDF letter generation
"""

# Django
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

# Standard Library
import os.path
from cStringIO import StringIO
from datetime import date
from itertools import groupby

# Third Party
import emoji
from fpdf import FPDF
from PyPDF2.merger import PdfFileMerger
from PyPDF2.pdf import PdfFileReader
from PyPDF2.utils import PdfReadError

# MuckRock
from muckrock.communication.models import MailCommunication


class PDF(FPDF):
    """Shared PDF settings"""

    def footer(self):
        """Add page number to the footer"""
        self.set_y(-25)
        self.set_font('Times', 'I', 10)
        self.cell(0, 10, 'Page {} of {{nb}}'.format(self.page_no()), 0, 0, 'C')

    def configure(self):
        """Configure common settings"""
        self.add_font(
            'DejaVu',
            '',
            os.path.join(settings.FONT_PATH, 'DejaVuSerif.ttf'),
            uni=True,
        )
        self.alias_nb_pages()
        self.add_page()


class MailPDF(PDF):
    """Base class for other mail classes to inherit from"""

    def __init__(self, comm, category, switch, amount=None):
        self.comm = comm
        self.appeal = category == 'a'
        self.switch = switch
        self.amount = amount
        super(MailPDF, self).__init__('P', 'pt', 'Letter')

    def header(self):
        """Add letterhead"""
        self.set_font('DejaVu', '', 10)
        email = self.comm.foia.get_request_email()
        text = (
            'MuckRock News\n'
            'DEPT MR {pk}\n'
            '411A Highland Ave\n'
            'Somerville, MA 02144-2516\n'
            '{email}'.format(
                pk=self.comm.foia.pk,
                email=email,
            )
        )
        width = self.get_string_width(email)
        self.set_xy(72 / 2, (72 * 0.6))
        self.multi_cell(width + 6, 13, text, 0, 'L')
        self.line(72 / 2, 1.55 * 72, 8 * 72, 1.55 * 72)
        self.ln(38)

    def generate(self):
        """Generate a PDF for a given FOIA"""
        self.configure()
        self._extra_generate()
        if self.appeal:
            law_name = self.comm.foia.jurisdiction.get_law_name(abbrev=True)
            self._extra_header(u'{} APPEAL'.format(law_name))
        self.set_font('DejaVu', '', 10)
        msg_body = self.comm.foia.render_msg_body(
            self.comm,
            appeal=self.appeal,
            switch=self.switch,
            include_address=self.include_address,
            payment=self.amount > 0,
        )
        # remove emoji's, as they break pdf rendering
        msg_body = emoji.get_emoji_regexp().sub(u'', msg_body)
        self.multi_cell(0, 13, msg_body.rstrip(), 0, 'L')

    def _extra_header(self, text):
        """Add an extra line to the header"""
        # pylint: disable=invalid-name
        x = self.get_x()
        y = self.get_y()
        self.set_font('Arial', 'b', 18)
        self.set_xy(3.5 * 72, (72 * 3) / 4)
        self.cell(0, 0, text)
        self.set_xy(x, y)

    def _extra_generate(self):
        """Hook for subclasses to override"""

    def prepare(self):
        """Prepare the PDF to be sent by appending attachments"""
        # generate the pdf and merge all pdf attachments
        # keep track of any problematic attachments
        self.generate()
        merger = PdfFileMerger(strict=False)
        merger.append(StringIO(self.output(dest='S')))
        files = []
        for file_ in self.comm.files.all():
            if file_.get_extension() == 'pdf':
                try:
                    pages = PdfFileReader(file_.ffile).getNumPages()
                    merger.append(file_.ffile)
                    files.append((file_, 'attached', pages))
                except (PdfReadError, ValueError):
                    files.append((file_, 'error', 0))
            else:
                files.append((file_, 'skipped', 0))
        single_pdf = StringIO()
        try:
            merger.write(single_pdf)
        except PdfReadError:
            return (None, None, files)

        # create the mail communication object
        mail, _ = MailCommunication.objects.update_or_create(
            communication=self.comm,
            defaults={
                'to_address': self.comm.foia.address,
                'sent_datetime': timezone.now(),
            }
        )
        single_pdf.seek(0)
        mail.pdf.save(
            '{}.pdf'.format(self.comm.pk),
            ContentFile(single_pdf.read()),
        )

        # return to begining of merged pdf before returning
        single_pdf.seek(0)

        return (single_pdf, self.page, files, mail)


class SnailMailPDF(MailPDF):
    """Custom PDF class for a snail mail task"""

    include_address = True

    def _extra_generate(self):
        """Add snail mail only features to PDF"""
        # Add shapes to assist staff in dealing with printed letters
        # New letter rectangle
        self.rect(6.8 * 72, 10, 1.2 * 72, 72 / 4, 'F')
        # Fold lines
        self.dashed_line(0, 4 * 72, 72 / 4, 4 * 72, 2, 2)
        self.dashed_line(8.25 * 72, 4 * 72, 8.5 * 72, 4 * 72, 2, 2)

        # Check notification
        if self.amount:
            self._extra_header(u'Check Enclosed for ${}'.format(self.amount))


class LobPDF(MailPDF):
    """Custom PDF class for mailing through Lob"""

    include_address = False

    def header(self):
        """Add letterhead"""
        if self.page_no() > 1:
            super(LobPDF, self).header()

    def _extra_generate(self):
        """Add Lob only features to PDF"""
        # whitespace for lob to insert address
        self.set_xy(72 * 0.4, (72 * 2.6))


class CoverPDF(PDF):
    """Custom PDF class for a cover page to bulk snail mail"""

    def __init__(self, info):
        self.info = info
        super(CoverPDF, self).__init__('P', 'pt', 'Letter')

    def header(self):
        """Add letterhead"""
        self.image(
            'muckrock/templates/lib/component/icon/logotype.png', 72 / 2,
            72 / 2, 3 * 72
        )
        self.line(72 / 2, 1.1 * 72, 8 * 72, 1.1 * 72)
        self.ln(70)

    def generate(self):
        """Generate a PDF cover page"""
        self.configure()
        self.set_font('DejaVu', '', 14)
        title = 'Bulk Snail Mail Cover Letter for {}'.format(date.today())
        self.cell(0, 0, title, 0, 1, 'C')
        self.ln(10)
        self.set_font('DejaVu', '', 10)
        lines = []
        grouped_info = groupby(
            self.info,
            lambda x: x[0].communication.foia.agency,
        )
        tab = u' ' * 8
        for agency, info in grouped_info:
            info = list(info)
            lines.append(
                u'\nAgency: {} - {} requests'.format(
                    agency.name,
                    len(info),
                )
            )
            for snail, pages, files in info:
                if pages is None:
                    lines.append(
                        u'\n{}□ Error: MR #{} - "{}" by {}'.format(
                            tab,
                            snail.communication.foia.pk,
                            snail.communication.foia.title,
                            snail.communication.from_user,
                        )
                    )
                else:
                    if snail.communication.foia.address:
                        warning = ''
                    else:
                        warning = 'Warning - No Address: '
                    lines.append(
                        u'\n{}□ {}MR #{} - "{}" by {} - {} pages'.format(
                            tab,
                            warning,
                            snail.communication.foia.pk,
                            snail.communication.foia.title,
                            snail.communication.from_user,
                            pages,
                        )
                    )
                if snail.category == 'p':
                    lines.append(
                        u'{}□ Write a {}check for ${:.2f}'.format(
                            2 * tab,
                            'CERTIFIED '
                            if snail.amount >= settings.CHECK_LIMIT else '',
                            snail.amount,
                        )
                    )
                for file_, status, pages in files:
                    if status == 'attached':
                        lines.append(
                            u'{}▣ Attached: {} - {} pages'.format(
                                2 * tab,
                                file_.name(),
                                pages,
                            )
                        )
                    elif status == 'skipped':
                        lines.append(
                            u'{}□ Print separately: {}'.format(
                                2 * tab, file_.name()
                            )
                        )
                    else:  # status == 'error'
                        lines.append(
                            u'{}□ Print separately (error): {}'.format(
                                2 * tab, file_.name()
                            )
                        )
        text = u'\n'.join(lines)
        self.multi_cell(0, 13, text, 0, 'L')
