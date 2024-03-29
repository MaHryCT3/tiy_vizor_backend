from typing import TYPE_CHECKING, Optional

from bs4 import BeautifulSoup

from app.models.models import CabinetPair, Pair, ScheduleDay, TeacherPair

if TYPE_CHECKING:
    from bs4.element import Tag


class ScheduleParser:
    """Парсит страницу официального расписания ТИУ"""

    def __init__(self, html: str):
        html_soup = BeautifulSoup(html, 'html.parser')
        self._main_table = html_soup.find('table', class_='main_table')

    def parse_schedule_days(self) -> list[ScheduleDay]:
        """Возвращает список дней расписания"""
        week_days_elements = self._get_week_days_elements()
        week_days = self._parse_week_days(week_days_elements)
        return week_days

    def parse_group_schedule(self) -> list[Pair]:
        """Возвращает список пар"""
        pairs_elements = self._get_pairs_elements()
        pairs = self._parse_group_pairs(pairs_elements)
        return pairs

    def parse_teacher_schedule(self) -> list[TeacherPair]:
        pairs_elements = self._get_pairs_elements()
        teachers_pairs = self._parse_teacher_pairs(pairs_elements)
        return teachers_pairs

    def parse_cabinet_schedule(self) -> list[CabinetPair]:
        pairs_elemnts = self._get_pairs_elements()
        cabinet_pairs = self._parse_cabinet_pairs(pairs_elemnts)
        return cabinet_pairs

    def _get_pairs_elements(self) -> list['Tag']:
        """Возвращает список элементов с парами"""
        return self._main_table.find_all('td', class_='urok')

    def _get_week_days_elements(self) -> list['Tag']:
        """Возвращает список элементов с днями недели"""
        return self._main_table.find_all('td', align='center')

    def _parse_week_days(self, week_days_elements: list['Tag']) -> list[ScheduleDay]:
        """Возвращает список дней недели"""
        week_days = []
        for element in week_days_elements:
            week_days.append(self._parse_week_day(element))
        return week_days

    def _parse_week_day(self, week_day_element: 'Tag') -> ScheduleDay:
        """Возвращает день недели"""
        date = week_day_element.next
        day_of_week = date.next.next
        week_type = day_of_week.next.next
        return ScheduleDay(
            date=date,
            day_of_week=day_of_week,
            week_type=week_type,
        )

    def _parse_group_pairs(self, pairs_elements: list['Tag']) -> list[Pair]:
        """Возвращает список пар"""
        return [self._parse_group_pair(element) for element in pairs_elements]

    def _parse_teacher_pairs(self, pairs_elements: list['Tag']) -> list[TeacherPair]:
        return [self._parse_teacher_pair(element) for element in pairs_elements]

    def _parse_cabinet_pairs(self, pairs_elements: list['Tag']) -> list[CabinetPair]:
        return [self._parse_cabinet_pair(element) for element in pairs_elements]

    def _parse_group_pair(self, pair_element: 'Tag') -> Pair:
        """Возвращает пару"""
        name = self._parse_pair_name(pair_element)
        teacher = self._parse_pair_teacher(pair_element)
        cabinet = self._parse_pair_cabinet(pair_element)
        is_replace = self._parse_pair_is_replaced(pair_element)
        not_learning = self._parse_not_learning(pair_element)
        is_wekeend = self._parse_is_weekend(pair_element)
        is_consultation, is_exam = self._parse_exam_or_consulatation(pair_element)
        return Pair(
            name=name,
            teacher=teacher,
            cabinet=cabinet,
            is_replace=is_replace,
            not_learning=not_learning,
            is_weekend=is_wekeend,
            is_consultation=is_consultation,
            is_exam=is_exam,
        )

    def _parse_teacher_pair(self, pair_element: 'Tag') -> TeacherPair:
        teacher_pair, group = self._parse_teacher_pair_and_group(pair_element)
        cabinet = self._parse_pair_cabinet(pair_element)
        is_replace = self._parse_pair_is_replaced(pair_element)
        return TeacherPair(
            name=teacher_pair,
            group=group,
            cabinet=cabinet,
            is_replace=is_replace,
        )

    def _parse_cabinet_pair(self, cab_pair_element: 'Tag') -> CabinetPair:
        pair, group, teacher = self._parse_pair_group_teacher_in_cabinet(cab_pair_element)
        is_replace = self._parse_pair_is_replaced(cab_pair_element)
        return CabinetPair(
            name=pair,
            group=group,
            teacher=teacher,
            is_replace=is_replace,
        )

    def _parse_pair_name(self, pair_element: 'Tag') -> str | None:
        name = pair_element.find('div', class_='disc')
        if not name:
            return ''  # Not None for frontend
        return name.text.strip()

    def _parse_pair_teacher(self, pair_element: 'Tag') -> str | None:
        teacher = pair_element.find('div', class_='prep')
        if not teacher:
            return ''  # Not None for frontend
        return teacher.text.strip()

    def _parse_pair_cabinet(self, pair_element: 'Tag') -> str | None:
        cabinet = pair_element.find('div', class_='cab')
        if not cabinet:
            return ''  # Not None for frontend
        return cabinet.text.strip()

    def _parse_pair_is_replaced(self, pair_element: 'Tag') -> bool:
        return True if pair_element.find('table', class_='zamena') else False

    def _parse_not_learning(self, pair_element: 'Tag') -> bool:
        text = pair_element.text.strip()
        if text == 'Не учатся':
            return True
        return False

    def _parse_is_weekend(self, pair_element: 'Tag') -> bool:
        text = pair_element.text.strip()
        if text == 'Каникулы':
            return True
        return False

    def _parse_exam_or_consulatation(self, pair_element: 'Tag') -> tuple[True, False]:
        exam_or_cons_element = pair_element.find('td', class_='head_ekz')
        if exam_or_cons_element:
            if 'консультация' in exam_or_cons_element.text.lower():
                return True, False
            else:
                return False, True
        else:
            return False, False

    def _parse_pair_is_consultation(self, pair_element: 'Tag') -> bool:
        pass

    def _parse_teacher_pair_and_group(self, pair_element: 'Tag') -> tuple[str, str]:
        full_name = self._get_pair_name(pair_element)
        if not full_name or full_name.text.isspace():
            return '', ''  # Not None for frontend
        separated_full_name = full_name.getText(':::')
        teacher_pair, group = separated_full_name.split(':::', maxsplit=2)
        return teacher_pair, group

    def _parse_pair_group_teacher_in_cabinet(self, cab_pair_element: 'Tag') -> tuple[str, str, str]:
        full_pair_name = self._get_pair_name(cab_pair_element)
        if not full_pair_name or full_pair_name.text.isspace():
            return '', '', ''  # Not None for frontend
        separated_full_name = full_pair_name.getText(':::')
        pair, group, teacher = separated_full_name.split(':::', maxsplit=3)
        return pair, group, teacher

    def _get_pair_name(self, pair_element: 'Tag') -> Optional['Tag']:
        full_name = pair_element.find('div', class_='disc')
        return full_name
