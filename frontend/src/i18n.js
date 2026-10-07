// Локализация интерфейса ru/kk. Переключатель языка в шапке; выбор запоминается в браузере.
import { reactive } from 'vue'
import { DEMO } from './demo/flag'

const messages = {
  ru: {
    app: { title: 'Маркетинг цен', logout: 'Выйти', notifications: 'Уведомления', noNotifications: 'Новых уведомлений нет' },
    menu: { requests: 'Заявки', suppliers: 'Пул поставщиков', catalog: 'Каталог цен', analytics: 'Аналитика', ma: 'Маркетинговый анализ' },
    footer: { info: 'Информация', contacts: 'Контакты', feedback: 'Жалобы и предложения', copy: 'АО НК «КазМунайГаз»' },
    login: { title: 'Вход в систему', username: 'Логин', password: 'Пароль', submit: 'Войти', hint: 'Используйте учётную запись домена или локальную учётную запись' },
    common: {
      save: 'Сохранить', cancel: 'Отмена', close: 'Закрыть', delete: 'Удалить', add: 'Добавить', next: 'Далее', back: 'Назад',
      search: 'Поиск', loading: 'Загрузка…', empty: 'Нет данных', yes: 'Да', no: 'Нет', confirm: 'Подтвердить',
      required: 'Обязательное поле', actions: 'Действия', download: 'Скачать', all: 'Все', reset: 'Сбросить',
      from: 'с', to: 'по', perPage: 'на странице', of: 'из', page: 'Стр.', error: 'Ошибка', saved: 'Сохранено',
    },
    status: {
      draft: 'Черновик', collecting_kp: 'Сбор КП', on_approval_dzo: 'На согласовании (ДЗО)',
      on_approval_db: 'На согласовании ДБ КМГ', on_final_approval: 'На утверждении директора ДБ КМГ',
      rework: 'На доработке', approved: 'Утверждено', cancelled: 'Аннулировано',
    },
    tabs: {
      draft: 'Черновики', collecting_kp: 'Сбор КП', on_approval: 'На согласовании', rework: 'На доработке',
      approved: 'Утверждено', cancelled: 'Аннулировано', all: 'Все', awaiting_me: 'Ожидают моего решения',
    },
    registry: {
      title: 'Маркетинговый анализ', create: 'Создать маркетинговый анализ', number: 'ID', dzo: 'ДЗО',
      subject: 'Предмет', initiator: 'Инициатор', author: 'Маркетолог', status: 'Статус', created: 'Создан',
      total: 'Сумма без НДС, ₸', searchPh: 'Номер, код АСУ НСИ или наименование', nsiCode: 'Код АСУ НСИ',
      empty: 'Маркетинговых анализов пока нет', emptyFiltered: 'По заданным условиям ничего не найдено',
      positions: 'поз.',
    },
    card: {
      new: 'Новый маркетинговый анализ', number: 'Маркетинговый анализ', iteration: 'Отправка №',
      steps: { general: 'Общие сведения', items: 'Товары', offers: 'Коммерческие предложения', approvers: 'Согласующие' },
      route: 'Маршрут согласования', history: 'История', pdf: 'Скачать маркетинговое заключение (PDF)',
      pdfPending: 'Заключение формируется…', pdfFailed: 'Не удалось сформировать заключение. Обратитесь к администратору.',
      submit: 'Отправить на согласование', cancelAnalysis: 'Аннулировать', deleteDraft: 'Удалить черновик',
      cancelConfirm: 'Аннулировать маркетинговый анализ? Действие необратимо.', deleteConfirm: 'Удалить черновик?',
      cancelReason: 'Причина аннулирования', readOnly: 'Документ на согласовании — редактирование недоступно',
      submitErrors: 'Анализ не готов к отправке:', submitted: 'Анализ отправлен на согласование',
      startCollecting: 'Перейти к сбору КП', regeneratePdf: 'Сформировать повторно', demoPdfNote: 'В демо файл не скачивается, заключение показано на странице. В системе это PDF с листом согласования, для файла хранится SHA-256.', reworkNote: 'Возвращено на доработку',
    },
    general: {
      initiator: 'Инициатор потребности (ФИО)', initiatorPh: 'Начните вводить ФИО', manual: 'Нет в справочнике — ввести вручную',
      fromDirectory: 'Выбрать из справочника', position: 'Должность', department: 'Подразделение', dzo: 'ДЗО',
      dzoLocked: 'ДЗО нельзя изменить после создания (номер уже присвоен)', create: 'Создать и продолжить',
      justification: 'Обоснование цены (общее)', author: 'Маркетолог', created: 'Дата создания',
    },
    items: {
      search: 'Товар по АСУ НСИ', searchPh: 'Код АСУ НСИ или наименование', nsiCode: 'Код АСУ НСИ', enstru: 'Код ЕНС ТРУ',
      name: 'Наименование', characteristics: 'Краткая характеристика', unit: 'Ед. изм.', quantity: 'Количество',
      place: 'Место поставки', term: 'Срок поставки', attachments: 'Вложения (ТС, чертежи)', addItem: 'Добавить позицию',
      empty: 'Добавьте хотя бы одну позицию', price: 'Маркет. цена за ед. без НДС, ₸', sum: 'Сумма без НДС, ₸',
      attach: 'Прикрепить файл', justification: 'Обоснование по позиции',
    },
    offers: {
      requestKp: 'Запросить КП', upload: 'Загрузить КП', calculate: 'Рассчитать маркетинговую цену',
      supplier: 'Поставщик', bin: 'БИН', date: 'Дата КП', currency: 'Валюта', vat: 'НДС', withVat: 'с НДС',
      withoutVat: 'без НДС', rate: 'Курс НБ РК', file: 'Файл КП', source: 'Источник', sourceSystem: 'Через систему',
      sourceManual: 'Вручную', pricePerUnit: 'Цена за ед.', priceKzt: 'Цена за ед., ₸ без НДС', empty: 'КП ещё не загружены',
      requestTitle: 'Запрос коммерческих предложений', requestHint: 'Выберите поставщиков из пула — им будет направлен запрос со ссылкой для подачи КП',
      message: 'Сопроводительный текст', send: 'Отправить запросы', sent: 'Запросы отправлены: {n}',
      uploadTitle: 'Загрузка коммерческого предложения', supplierName: 'Наименование поставщика',
      supplierPick: 'Поставщик из пула', pricesTitle: 'Цены по позициям', fileHint: 'PDF, DOC, DOCX, XLS, XLSX, JPG, PNG',
      analytics: 'Аналитика', participants: 'Участников', chart: 'Цены участников, ₸ без НДС', min: 'Мин.', max: 'Макс.',
      avg: 'Среднее', marketing: 'Маркетинговая цена', kmgAvg: 'Средняя по группе КМГ', deviation: 'Отклонение от средней КМГ',
      history: 'Исторические цены (каталог цен)', noHistory: 'Исторических данных нет', summary: 'Сводка по выбранным ценам',
      total: 'Итого без НДС', method: 'Методика', methods: { average: 'среднее арифметическое', min: 'минимальная цена' },
      notCalculated: 'Не рассчитано', threshold: 'Отклонение превышает порог',
    },
    approvers: {
      stage1: 'Этап 1. Согласующие ДЗО', stage1Hint: 'Добавьте согласующих и задайте порядок перетаскиванием',
      add: 'Добавить согласующего', searchPh: 'ФИО сотрудника', empty: 'Согласующие не выбраны',
      stage2: 'Этап 2. Департамент бюджетирования КМГ', stage3: 'Этап 3. Директор департамента бюджетирования КМГ',
      fixed: 'Фиксированный этап', up: 'Выше', down: 'Ниже', saveOrder: 'Сохранить список',
    },
    route: {
      stage: 'Этап', assignee: 'Исполнитель', decision: 'Решение', date: 'Дата', comment: 'Комментарий',
      notSubmitted: 'Маршрут сформируется после отправки на согласование', current: 'Текущий шаг',
      stepStatus: { waiting: 'Ожидает очереди', pending: 'На рассмотрении', approved: 'Согласовано', returned: 'Возвращено', skipped: 'Не рассматривалось' },
    },
    decision: {
      title: 'Решение по маркетинговому анализу', approve: 'Согласовать', approveFinal: 'Утвердить', rework: 'Вернуть на доработку',
      comment: 'Комментарий', commentOptional: 'Комментарий (необязательно)', commentRequired: 'Укажите причину возврата',
      awaiting: 'Ожидает вашего решения', done: 'Решение принято',
    },
    history: { events: 'Журнал событий', user: 'Пользователь', action: 'Действие' },
    errors: {
      network: 'Сервер недоступен. Повторите попытку позже.', forbidden: 'Недостаточно прав', notFound: 'Документ не найден или нет доступа',
      status_changed: 'Документ уже изменён другим пользователем. Обновите страницу.',
      step_already_processed: 'Шаг уже обработан. Обновите страницу.', comment_required: 'При возврате на доработку комментарий обязателен',
    },
    demo: {
      banner: 'Демо-версия: тестовые данные, сервер не нужен. Изменения сохраняются только в вашем браузере.',
      switchUser: 'Войти как', reset: 'Сбросить демо', pickUser: 'Выберите пользователя — пароль подставится автоматически',
      resetDone: 'Демо-данные восстановлены',
    },
    placeholder: { title: 'Раздел действующего портала', text: 'Раздел не входит в MVP подмодуля и показан для навигации.' },
    events: {
      created: 'Создан', updated: 'Изменены общие сведения', item_added: 'Добавлена позиция', item_updated: 'Изменена позиция',
      item_deleted: 'Удалена позиция', attachment_added: 'Добавлено вложение', attachment_deleted: 'Удалено вложение',
      offer_uploaded: 'Загружено КП', offer_received: 'Получено КП от поставщика', offer_deleted: 'Удалено КП',
      kp_requested: 'Направлены запросы КП', calculated: 'Рассчитана маркетинговая цена', approvers_set: 'Изменены согласующие',
      collecting_started: 'Начат сбор КП', submitted: 'Отправлен на согласование', step_approved: 'Согласовано',
      returned_for_rework: 'Возвращён на доработку', approved: 'Утверждён', cancelled: 'Аннулирован', pdf_downloaded: 'Скачано заключение',
    },
    kp: { title: 'Подача коммерческого предложения', submit: 'Отправить КП', done: 'Спасибо! Коммерческое предложение принято.' },
  },
  kk: {
    app: { title: 'Баға маркетингі', logout: 'Шығу', notifications: 'Хабарламалар', noNotifications: 'Жаңа хабарламалар жоқ' },
    menu: { requests: 'Өтінімдер', suppliers: 'Жеткізушілер пулы', catalog: 'Баға каталогы', analytics: 'Талдау', ma: 'Маркетингтік талдау' },
    footer: { info: 'Ақпарат', contacts: 'Байланыстар', feedback: 'Шағымдар мен ұсыныстар', copy: '«ҚазМұнайГаз» ҰК АҚ' },
    login: { title: 'Жүйеге кіру', username: 'Логин', password: 'Құпиясөз', submit: 'Кіру', hint: 'Домендік немесе жергілікті есептік жазбаны пайдаланыңыз' },
    common: {
      save: 'Сақтау', cancel: 'Болдырмау', close: 'Жабу', delete: 'Жою', add: 'Қосу', next: 'Әрі қарай', back: 'Артқа',
      search: 'Іздеу', loading: 'Жүктелуде…', empty: 'Деректер жоқ', yes: 'Иә', no: 'Жоқ', confirm: 'Растау',
      required: 'Міндетті өріс', actions: 'Әрекеттер', download: 'Жүктеп алу', all: 'Барлығы', reset: 'Тазарту',
      from: 'бастап', to: 'дейін', perPage: 'бетте', of: '/', page: 'Бет', error: 'Қате', saved: 'Сақталды',
    },
    status: {
      draft: 'Жоба', collecting_kp: 'КҰ жинау', on_approval_dzo: 'Келісуде (ЕТҰ)',
      on_approval_db: 'ҚМГ БД келісуде', on_final_approval: 'ҚМГ БД директорының бекітуінде',
      rework: 'Пысықтауда', approved: 'Бекітілді', cancelled: 'Күші жойылды',
    },
    tabs: {
      draft: 'Жобалар', collecting_kp: 'КҰ жинау', on_approval: 'Келісуде', rework: 'Пысықтауда',
      approved: 'Бекітілді', cancelled: 'Күші жойылды', all: 'Барлығы', awaiting_me: 'Менің шешімімді күтуде',
    },
    registry: {
      title: 'Маркетингтік талдау', create: 'Маркетингтік талдау құру', number: 'ID', dzo: 'ЕТҰ',
      subject: 'Пәні', initiator: 'Бастамашы', author: 'Маркетолог', status: 'Мәртебе', created: 'Құрылды',
      total: 'ҚҚС-сыз сома, ₸', searchPh: 'Нөмір, НАЖ АБЖ коды немесе атауы', nsiCode: 'НАЖ АБЖ коды',
      empty: 'Маркетингтік талдаулар әлі жоқ', emptyFiltered: 'Берілген шарттар бойынша ештеңе табылмады',
      positions: 'айқ.',
    },
    card: {
      new: 'Жаңа маркетингтік талдау', number: 'Маркетингтік талдау', iteration: 'Жіберу №',
      steps: { general: 'Жалпы мәліметтер', items: 'Тауарлар', offers: 'Коммерциялық ұсыныстар', approvers: 'Келісушілер' },
      route: 'Келісу бағыты', history: 'Тарих', pdf: 'Маркетингтік қорытындыны жүктеп алу (PDF)',
      pdfPending: 'Қорытынды қалыптастырылуда…', pdfFailed: 'Қорытындыны қалыптастыру мүмкін болмады. Әкімшіге хабарласыңыз.',
      submit: 'Келісуге жіберу', cancelAnalysis: 'Күшін жою', deleteDraft: 'Жобаны жою',
      cancelConfirm: 'Маркетингтік талдаудың күшін жою керек пе? Әрекетті қайтару мүмкін емес.', deleteConfirm: 'Жобаны жою керек пе?',
      cancelReason: 'Күшін жою себебі', readOnly: 'Құжат келісуде — өңдеу қолжетімсіз',
      submitErrors: 'Талдау жіберуге дайын емес:', submitted: 'Талдау келісуге жіберілді',
      startCollecting: 'КҰ жинауға өту', regeneratePdf: 'Қайта қалыптастыру', demoPdfNote: 'Демода файл жүктелмейді, қорытынды бетте көрсетілген. Жүйеде бұл келісу парағы бар PDF, файл үшін SHA-256 сақталады.', reworkNote: 'Пысықтауға қайтарылды',
    },
    general: {
      initiator: 'Қажеттілік бастамашысы (ТАӘ)', initiatorPh: 'ТАӘ енгізе бастаңыз', manual: 'Анықтамалықта жоқ — қолмен енгізу',
      fromDirectory: 'Анықтамалықтан таңдау', position: 'Лауазымы', department: 'Бөлімше', dzo: 'ЕТҰ',
      dzoLocked: 'Құрылғаннан кейін ЕТҰ өзгертуге болмайды (нөмір берілді)', create: 'Құру және жалғастыру',
      justification: 'Бағаның негіздемесі (жалпы)', author: 'Маркетолог', created: 'Құрылған күні',
    },
    items: {
      search: 'НАЖ АБЖ бойынша тауар', searchPh: 'НАЖ АБЖ коды немесе атауы', nsiCode: 'НАЖ АБЖ коды', enstru: 'ТЖҚ БНА коды',
      name: 'Атауы', characteristics: 'Қысқаша сипаттамасы', unit: 'Өлш. бірл.', quantity: 'Саны',
      place: 'Жеткізу орны', term: 'Жеткізу мерзімі', attachments: 'Тіркемелер (ТС, сызбалар)', addItem: 'Айқындама қосу',
      empty: 'Кемінде бір айқындама қосыңыз', price: 'ҚҚС-сыз бірлік маркет. бағасы, ₸', sum: 'ҚҚС-сыз сома, ₸',
      attach: 'Файл тіркеу', justification: 'Айқындама бойынша негіздеме',
    },
    offers: {
      requestKp: 'КҰ сұрату', upload: 'КҰ жүктеу', calculate: 'Маркетингтік бағаны есептеу',
      supplier: 'Жеткізуші', bin: 'БСН', date: 'КҰ күні', currency: 'Валюта', vat: 'ҚҚС', withVat: 'ҚҚС-пен',
      withoutVat: 'ҚҚС-сыз', rate: 'ҚР ҰБ бағамы', file: 'КҰ файлы', source: 'Дереккөз', sourceSystem: 'Жүйе арқылы',
      sourceManual: 'Қолмен', pricePerUnit: 'Бірлік бағасы', priceKzt: 'Бірлік бағасы, ₸ ҚҚС-сыз', empty: 'КҰ әлі жүктелмеген',
      requestTitle: 'Коммерциялық ұсыныстарды сұрату', requestHint: 'Пулдан жеткізушілерді таңдаңыз — оларға КҰ беру сілтемесі бар сұрау жіберіледі',
      message: 'Ілеспе мәтін', send: 'Сұрауларды жіберу', sent: 'Жіберілген сұраулар: {n}',
      uploadTitle: 'Коммерциялық ұсынысты жүктеу', supplierName: 'Жеткізушінің атауы',
      supplierPick: 'Пулдағы жеткізуші', pricesTitle: 'Айқындамалар бойынша бағалар', fileHint: 'PDF, DOC, DOCX, XLS, XLSX, JPG, PNG',
      analytics: 'Талдау', participants: 'Қатысушылар', chart: 'Қатысушылардың бағалары, ₸ ҚҚС-сыз', min: 'Ең аз', max: 'Ең көп',
      avg: 'Орташа', marketing: 'Маркетингтік баға', kmgAvg: 'ҚМГ тобы бойынша орташа', deviation: 'ҚМГ орташасынан ауытқу',
      history: 'Тарихи бағалар (баға каталогы)', noHistory: 'Тарихи деректер жоқ', summary: 'Таңдалған бағалар бойынша жиынтық',
      total: 'ҚҚС-сыз барлығы', method: 'Әдістеме', methods: { average: 'орташа арифметикалық', min: 'ең төменгі баға' },
      notCalculated: 'Есептелмеген', threshold: 'Ауытқу шектен асады',
    },
    approvers: {
      stage1: '1-кезең. ЕТҰ келісушілері', stage1Hint: 'Келісушілерді қосып, ретін сүйреп орнатыңыз',
      add: 'Келісуші қосу', searchPh: 'Қызметкердің ТАӘ', empty: 'Келісушілер таңдалмаған',
      stage2: '2-кезең. ҚМГ Бюджеттеу департаменті', stage3: '3-кезең. ҚМГ Бюджеттеу департаментінің директоры',
      fixed: 'Тұрақты кезең', up: 'Жоғары', down: 'Төмен', saveOrder: 'Тізімді сақтау',
    },
    route: {
      stage: 'Кезең', assignee: 'Орындаушы', decision: 'Шешім', date: 'Күні', comment: 'Түсініктеме',
      notSubmitted: 'Бағыт келісуге жібергеннен кейін қалыптасады', current: 'Ағымдағы қадам',
      stepStatus: { waiting: 'Кезегін күтуде', pending: 'Қаралуда', approved: 'Келісілді', returned: 'Қайтарылды', skipped: 'Қаралмады' },
    },
    decision: {
      title: 'Маркетингтік талдау бойынша шешім', approve: 'Келісу', approveFinal: 'Бекіту', rework: 'Пысықтауға қайтару',
      comment: 'Түсініктеме', commentOptional: 'Түсініктеме (міндетті емес)', commentRequired: 'Қайтару себебін көрсетіңіз',
      awaiting: 'Сіздің шешіміңізді күтуде', done: 'Шешім қабылданды',
    },
    history: { events: 'Оқиғалар журналы', user: 'Пайдаланушы', action: 'Әрекет' },
    errors: {
      network: 'Сервер қолжетімсіз. Кейінірек қайталап көріңіз.', forbidden: 'Құқықтар жеткіліксіз', notFound: 'Құжат табылмады немесе қолжетімсіз',
      status_changed: 'Құжатты басқа пайдаланушы өзгертті. Бетті жаңартыңыз.',
      step_already_processed: 'Қадам өңделіп қойған. Бетті жаңартыңыз.', comment_required: 'Пысықтауға қайтарғанда түсініктеме міндетті',
    },
    demo: {
      banner: 'Демо-нұсқа: сынақ деректері, сервер қажет емес. Өзгерістер тек сіздің браузеріңізде сақталады.',
      switchUser: 'Кім ретінде кіру', reset: 'Демоны қалпына келтіру', pickUser: 'Пайдаланушыны таңдаңыз — құпиясөз автоматты түрде қойылады',
      resetDone: 'Демо-деректер қалпына келтірілді',
    },
    placeholder: { title: 'Қолданыстағы портал бөлімі', text: 'Бөлім ішкі модуль MVP құрамына кірмейді және навигация үшін көрсетілген.' },
    events: {
      created: 'Құрылды', updated: 'Жалпы мәліметтер өзгертілді', item_added: 'Айқындама қосылды', item_updated: 'Айқындама өзгертілді',
      item_deleted: 'Айқындама жойылды', attachment_added: 'Тіркеме қосылды', attachment_deleted: 'Тіркеме жойылды',
      offer_uploaded: 'КҰ жүктелді', offer_received: 'Жеткізушіден КҰ алынды', offer_deleted: 'КҰ жойылды',
      kp_requested: 'КҰ сұраулары жіберілді', calculated: 'Маркетингтік баға есептелді', approvers_set: 'Келісушілер өзгертілді',
      collecting_started: 'КҰ жинау басталды', submitted: 'Келісуге жіберілді', step_approved: 'Келісілді',
      returned_for_rework: 'Пысықтауға қайтарылды', approved: 'Бекітілді', cancelled: 'Күші жойылды', pdf_downloaded: 'Қорытынды жүктеп алынды',
    },
    kp: { title: 'Коммерциялық ұсыныс беру', submit: 'КҰ жіберу', done: 'Рахмет! Коммерциялық ұсыныс қабылданды.' },
  },
}

// В публичном демо — условные наименования вместо реальной организации.
function neutralize(node) {
  for (const [k, v] of Object.entries(node)) {
    if (typeof v === 'object') neutralize(v)
    else node[k] = v.replace('АО НК «КазМунайГаз»', 'Демо-стенд').replace('«ҚазМұнайГаз» ҰК АҚ', 'Демо-стенд')
      .replace(/КМГ/g, 'Холдинга').replace(/ҚМГ/g, 'Холдинг')
  }
}
if (DEMO) neutralize(messages)

function storedLocale() {
  try { return localStorage.getItem('price.locale') } catch { return null }
}

export const i18nState = reactive({ locale: storedLocale() === 'kk' ? 'kk' : 'ru' })

function lookup(locale, key) {
  return key.split('.').reduce((acc, part) => (acc && acc[part] !== undefined ? acc[part] : undefined), messages[locale])
}

export function t(key, params) {
  let value = lookup(i18nState.locale, key)
  if (value === undefined) value = lookup('ru', key)
  if (value === undefined) return key
  if (params) Object.entries(params).forEach(([k, v]) => { value = value.replace(`{${k}}`, v) })
  return value
}

export function setLocale(locale) {
  i18nState.locale = locale
  try { localStorage.setItem('price.locale', locale) } catch { /* приватный режим */ }
  document.documentElement.lang = locale
}

export const i18n = {
  install(app) {
    app.config.globalProperties.$t = t
    app.config.globalProperties.$i18n = i18nState
  },
}

// Ошибка API → локализованный текст: известный код ошибки, иначе текст с backend.
export function errorText(err) {
  if (!err) return ''
  if (!err.status) return t('errors.network')
  if (err.code && lookup(i18nState.locale, `errors.${err.code}`)) return t(`errors.${err.code}`)
  if (err.status === 403 && !err.code) return t('errors.forbidden')
  if (err.status === 404 && !err.code) return t('errors.notFound')
  return err.message
}

export { messages }
