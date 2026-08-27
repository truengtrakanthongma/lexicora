/**
 * Lexicora — ตัวรับข้อมูลการเรียนแบบเรียลไทม์
 *
 * วิธีติดตั้ง (ทำครั้งเดียว)
 *   1. เปิด Google Sheet ของเกม → เมนู ส่วนขยาย → Apps Script
 *   2. ลบโค้ดเดิมทิ้ง แล้ววางไฟล์นี้ทั้งไฟล์
 *   3. กด Run เลือกฟังก์ชัน setup  (ครั้งแรกจะขออนุญาต ให้กดอนุญาต)
 *   4. กด Deploy → New deployment → ประเภท Web app
 *        Execute as        : Me
 *        Who has access    : Anyone
 *   5. คัดลอก Web app URL ที่ได้ ไปใส่ในเกม
 *
 * ถ้าแก้โค้ดนี้ภายหลัง ต้อง Deploy → Manage deployments → แก้เป็น New version
 * ไม่งั้นเกมจะยังเรียกโค้ดเวอร์ชันเดิมอยู่
 */

var TABS = {
  events:  { name: 'เหตุการณ์ทั้งหมด',
             head: ['เวลา','ชื่อ','ชั้น','เลขที่','อาชีพ','ด่าน','เรื่อง',
                    'เหตุการณ์','รายละเอียด','ค่า 1','ค่า 2','ค่า 3','รหัสเครื่อง'] },
  answers: { name: 'ทุกคำตอบ',
             head: ['เวลา','ชื่อ','ชั้น','เลขที่','ด่าน','เรื่อง','สถานการณ์','รูปแบบข้อ',
                    'โจทย์','ตอบว่า','เฉลย','ถูก/ผิด','วินาทีที่ใช้','รหัสเครื่อง'] },
  tests:   { name: 'คะแนนสอบ',
             head: ['เวลา','ชื่อ','ชั้น','เลขที่','ด่าน','เรื่อง','ก่อน/หลังเรียน','ครั้งที่',
                    'คะแนน','เต็ม','ร้อยละ','ไวยากรณ์','คำศัพท์','นาทีทำข้อสอบ','นาทีในด่าน',
                    'ผลรายข้อ','รหัสเครื่อง'] },
};

/** สร้างและจัดรูปแบบแผ่นงานทั้งหมด — รันครั้งเดียวตอนติดตั้ง */
function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  Object.keys(TABS).forEach(function (key) {
    var spec = TABS[key];
    var sh = ss.getSheetByName(spec.name) || ss.insertSheet(spec.name);
    sh.clear();
    var head = sh.getRange(1, 1, 1, spec.head.length);
    head.setValues([spec.head]);
    head.setFontWeight('bold')
        .setBackground('#4a2f1e')
        .setFontColor('#ffeec4')
        .setVerticalAlignment('middle');
    sh.setFrozenRows(1);
    sh.setRowHeight(1, 34);
    sh.getRange(1, 1, sh.getMaxRows(), spec.head.length)
      .setFontFamily('Sarabun');
    for (var c = 1; c <= spec.head.length; c++) sh.autoResizeColumn(c);
    // แถบสีสลับให้อ่านง่ายเวลาข้อมูลเยอะ
    try {
      sh.getRange(2, 1, sh.getMaxRows() - 1, spec.head.length)
        .applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY);
    } catch (e) { /* มีแถบสีอยู่แล้ว */ }
  });

  buildDashboard(ss);

  // แผ่นเปล่าที่ Drive สร้างมาตอนแรก ไม่ใช้แล้ว
  var first = ss.getSheets()[0];
  if (Object.keys(TABS).every(function (k) { return TABS[k].name !== first.getName(); }) &&
      first.getName() !== 'สรุปภาพรวม' && ss.getSheets().length > 1) {
    ss.deleteSheet(first);
  }
  ss.setActiveSheet(ss.getSheetByName('สรุปภาพรวม'));
  return 'ติดตั้งเรียบร้อย';
}

/** หน้าสรุปที่คำนวณตัวเองจากข้อมูลดิบ */
function buildDashboard(ss) {
  var name = 'สรุปภาพรวม';
  var sh = ss.getSheetByName(name) || ss.insertSheet(name, 0);
  sh.clear();
  var A = TABS.answers.name, T = TABS.tests.name;

  sh.getRange('A1').setValue('Lexicora — สรุปภาพรวม')
    .setFontSize(18).setFontWeight('bold').setFontColor('#4a2f1e');
  sh.getRange('A2').setValue('ตัวเลขทุกช่องคำนวณสดจากข้อมูลดิบ ไม่ต้องกดอะไร')
    .setFontColor('#6b5238');

  var rows = [
    ['จำนวนนักเรียน',        '=IFERROR(COUNTA(UNIQUE(FILTER(\'' + T + '\'!B2:B,\'' + T + '\'!B2:B<>""))),0)'],
    ['จำนวนคำตอบทั้งหมด',    '=IFERROR(COUNTA(\'' + A + '\'!A2:A),0)'],
    ['ตอบถูก',               '=IFERROR(COUNTIF(\'' + A + '\'!L2:L,"ถูก"),0)'],
    ['ร้อยละความถูกต้อง',    '=IFERROR(ROUND(B6/B5*100,2),0)'],
    ['สอบก่อนเรียน (ครั้ง)', '=IFERROR(COUNTIF(\'' + T + '\'!G2:G,"ก่อนเรียน"),0)'],
    ['สอบหลังเรียน (ครั้ง)', '=IFERROR(COUNTIF(\'' + T + '\'!G2:G,"หลังเรียน"),0)'],
    ['ค่าเฉลี่ยก่อนเรียน (%)','=IFERROR(ROUND(AVERAGEIF(\'' + T + '\'!G2:G,"ก่อนเรียน",\'' + T + '\'!K2:K),2),0)'],
    ['ค่าเฉลี่ยหลังเรียน (%)','=IFERROR(ROUND(AVERAGEIF(\'' + T + '\'!G2:G,"หลังเรียน",\'' + T + '\'!K2:K),2),0)'],
    ['ผลต่าง (%)',           '=IFERROR(B11-B10,0)'],
  ];
  sh.getRange(4, 1, rows.length, 2).setValues(rows);
  sh.getRange(4, 1, rows.length, 1).setFontWeight('bold').setFontColor('#4a2f1e');
  sh.getRange(4, 2, rows.length, 1).setHorizontalAlignment('right').setFontSize(13);
  sh.getRange(4, 1, rows.length, 2).setFontFamily('Sarabun');

  sh.getRange('D4').setValue('ความถูกต้องแยกตามเรื่อง').setFontWeight('bold').setFontColor('#4a2f1e');
  sh.getRange('D5').setFormula(
    '=IFERROR(QUERY(\'' + A + '\'!F2:L, "select F, count(L), sum(case when L = \'ถูก\' then 1 else 0 end) ' +
    'where F is not null group by F label F \'เรื่อง\', count(L) \'ตอบทั้งหมด\', ' +
    'sum(case when L = \'ถูก\' then 1 else 0 end) \'ถูก\'", 0), "ยังไม่มีข้อมูล")');

  sh.setColumnWidth(1, 210);
  sh.setColumnWidth(2, 110);
  sh.setColumnWidth(3, 30);
  sh.setFrozenRows(3);
}

/** เกมส่งข้อมูลเข้ามาที่นี่ */
function doPost(e) {
  var out = { ok: false };
  try {
    var body = JSON.parse(e.postData.contents);
    var list = body.events || [body];
    // ล็อกกันสองเครื่องเขียนชนกันตอนทั้งห้องเล่นพร้อมกัน
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var buckets = { events: [], answers: [], tests: [] };
      // Skip anything already filed. The game resends when it cannot confirm a
      // save, and a browser is not always allowed to read this script's reply —
      // so a successful write can look like a failure and come back again.
      var cache = CacheService.getScriptCache();
      var seen = 0;
      list.forEach(function (ev) {
        if (ev.id) {
          if (cache.get('ev_' + ev.id)) { seen++; return; }
          cache.put('ev_' + ev.id, '1', 21600);   // remember for six hours
        }
        var t = rowsFor(ev);
        if (t) buckets[t.tab].push(t.row);
      });
      Object.keys(buckets).forEach(function (k) {
        if (!buckets[k].length) return;
        var sh = ss.getSheetByName(TABS[k].name);
        if (!sh) return;
        sh.getRange(sh.getLastRow() + 1, 1, buckets[k].length, buckets[k][0].length)
          .setValues(buckets[k]);
      });
      out = { ok: true, saved: list.length - seen, duplicates: seen };
    } finally { lock.releaseLock(); }
  } catch (err) {
    out = { ok: false, error: String(err) };
  }
  return ContentService.createTextOutput(JSON.stringify(out))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * เปิดเปล่าๆ = เช็คว่าติดตั้งถูกไหม
 * ?board=1&cb=ชื่อฟังก์ชัน = ส่งกระดานคะแนนกลับไปให้เกม
 *
 * ตอบกลับเป็น JSONP ไม่ใช่ JSON ธรรมดา เพราะ Apps Script เปลี่ยนเส้นทางไป
 * googleusercontent.com ซึ่งบางกรณีเบราว์เซอร์บล็อกการอ่านข้ามโดเมน
 * JSONP ทำงานได้ทุกกรณีและกระดานนี้เป็นข้อมูลอ่านอย่างเดียว
 */
function doGet(e) {
  var q = (e && e.parameter) || {};
  if (!q.board) {
    return ContentService.createTextOutput(
      'Lexicora พร้อมรับข้อมูลแล้ว · ' + new Date().toLocaleString('th-TH'));
  }
  var payload = JSON.stringify(buildBoard());
  if (q.cb) {
    return ContentService.createTextOutput(q.cb + '(' + payload + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService.createTextOutput(payload)
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * อันดับแยกรายด่าน — เพื่อให้มีผู้ชนะหลายคน ไม่ใช่เก่งสุดคนเดียวได้ไปทั้งหมด
 * เรียงตาม: ผ่านเกณฑ์ก่อน → คะแนนสอบหลังเรียนมากกว่า → ใช้เวลาในด่านน้อยกว่า
 * ใช้ผลสอบ "ครั้งแรก" ของแต่ละคนต่อด่าน เพื่อไม่ให้คนสอบซ้ำหลายรอบได้เปรียบ
 */
function buildBoard() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(TABS.tests.name);
  if (!sh || sh.getLastRow() < 2) return { zones: {}, at: Date.now() };
  var v = sh.getRange(2, 1, sh.getLastRow() - 1, 17).getValues();
  var best = {};        // ด่าน → คน → ผลที่ดีที่สุด
  v.forEach(function (r) {
    if (String(r[6]) !== 'หลังเรียน') return;          // เอาเฉพาะสอบหลังเรียน
    var zone = Number(r[4]); if (!zone) return;
    var key = [r[2], r[3], r[1]].join('|');            // ชั้น|เลขที่|ชื่อ
    var row = {
      name: String(r[1]), klass: String(r[2]), no: String(r[3]),
      score: Number(r[8]) || 0, total: Number(r[9]) || 0,
      pct: Number(r[10]) || 0, minutes: Number(r[14]) || 0,
      attempt: Number(r[7]) || 1,
    };
    best[zone] = best[zone] || {};
    var cur = best[zone][key];
    // ครั้งแรกเท่านั้น: ถ้ามีอยู่แล้วและครั้งนั้นเก่ากว่า ให้เก็บของเดิมไว้
    if (!cur || row.attempt < cur.attempt) best[zone][key] = row;
  });

  var out = {};
  Object.keys(best).forEach(function (zone) {
    var list = Object.keys(best[zone]).map(function (k) { return best[zone][k]; });
    list.sort(function (a, b) {
      var pa = a.pct >= 80 ? 1 : 0, pb = b.pct >= 80 ? 1 : 0;
      if (pa !== pb) return pb - pa;                    // ผ่านเกณฑ์มาก่อน
      if (b.score !== a.score) return b.score - a.score; // คะแนนมากกว่า
      return (a.minutes || 1e9) - (b.minutes || 1e9);    // แล้วเร็วกว่า
    });
    out[zone] = list.slice(0, 10).map(function (r, i) {
      return { rank: i + 1, name: r.name, klass: r.klass, no: r.no,
               score: r.score, total: r.total, pct: r.pct,
               minutes: r.minutes, passed: r.pct >= 80 };
    });
  });
  return { zones: out, at: Date.now() };
}

/** แปลงเหตุการณ์หนึ่งอันเป็นแถวของแผ่นที่เหมาะสม */
function rowsFor(ev) {
  var when = ev.at ? new Date(ev.at) : new Date();
  var who = [ev.name || '', ev.klass || '', ev.no || ''];

  if (ev.type === 'answer') {
    return { tab: 'answers', row: [when].concat(who,
      [ev.zone, ev.topic, ev.context || '', ev.format || '',
       ev.question || '', ev.chose || '', ev.answer || '',
       ev.correct ? 'ถูก' : 'ผิด', ev.seconds || '', ev.device || '']) };
  }
  if (ev.type === 'test') {
    return { tab: 'tests', row: [when].concat(who,
      [ev.zone, ev.topic, ev.phase === 'pre' ? 'ก่อนเรียน' : 'หลังเรียน',
       ev.attempt || 1, ev.score, ev.total,
       ev.total ? Math.round(ev.score / ev.total * 10000) / 100 : 0,
       ev.grammar || '', ev.vocab || '', ev.minutes || '', ev.zoneMinutes || '',
       "'" + (ev.hits || ''), ev.device || '']) };
  }
  return { tab: 'events', row: [when].concat(who,
    [ev.role || '', ev.zone === undefined ? '' : ev.zone, ev.topic || '',
     ev.type || '', ev.detail || '', ev.v1 === undefined ? '' : ev.v1,
     ev.v2 === undefined ? '' : ev.v2, ev.v3 === undefined ? '' : ev.v3,
     ev.device || '']) };
}
