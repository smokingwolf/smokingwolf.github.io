#!/usr/bin/perl
use CGI::Carp qw(fatalsToBrowser);


$cgi_name = "./ninki_vote.cgi";

$dir = "vote_log";
$log = "$dir/Log_Vote.cgi";

$mailto = 'dustbox@silversecond.net';
$mail = 'FROM_SILVERSECOND@silversecond.net'; #ダミーメールアドレス

# 投票終了ページ
$location_end = "http://www.silversecond.com/WolfRPGEditor/Contest/thanks_v_end.shtml"; 

# ●もし投票終了なら終了ページへ
if($end_Flag){
	print "Location: $location_end\n\n";
	exit;
}






#
# ◆入力値を読み取る
#
if ($ENV{'REQUEST_METHOD'} eq "POST") {
	require "jcode.pl";
	read(STDIN, $query_string, $ENV{'CONTENT_LENGTH'});
	@pairs = split(/&/, $query_string);
	#print "$query_string<br><br>";
	foreach $pair (@pairs) {
		($sname, $value) = split(/=/, $pair);
		$sname =~ tr/+/ /;
		$sname =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		&jcode'convert(*sname,'sjis'); # sjisだとまずい気がするが日本語は入らない
		$value =~ tr/+/ /;
		$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		&jcode'convert(*value,'sjis');
		$value =~ s/\t/ /g;
		$value =~ s/\r\n/\n/g;
		$value =~ s/\r/\n/g;
		$value =~ s/\n/<BR>/g;
		$value =~ s/</&lt;/g;
		if ($FORM{$sname} eq "") {
			$value =~ s/</&lt;/g;
			$value =~ s/>/&gt;/g;
			$FORM{$sname} = $value;
			$FORM[$cnt++] = $sname;
			#print "$sname = $value<BR>";
		} else {
			$FORM{$sname} .= (" " . $value);
		}
	}
	
	
	
	$vote_code = $FORM{'VOTE'};
	$user_id = $FORM{'ID'};
	
	if( $FORM{'VOTE'} eq ""){
		print "<BR><BR><BR>ERROR：投票コードがありません。このエラーが表示される場合、すでに投票が終わっている場合がございます。".$FORM{'VOTE'}."<BR>".$FORM{'ID'};
	
		exit;
	}
	
	# onになっているキャラクター番号を得てキャラ番号＆メッセージ部を作る
	$selected_chara = "";
	$main_message = "";
	foreach $formname (keys %FORM) {
		if( $FORM{$formname} eq "on" && $formname =~ /^chara_/ ){ # chara_4などがonになっている
			($head, $number) = split(/_/, $formname);
			
			#print "$number = ON !!!!<BR>";
			$selected_chara .= "$number,";
			$tname = "text". $number; #text2などに各キャラ応援メッセージが入っている
			$main_message .= "$number<>$FORM{$tname}<>";
		}
	}
	
	# ここからファイルへ書き込み
	
	#●ファイルの読み込み、比較
	open(DB,"$vote_code/Log_1.cgi");@comlist1 = <DB>;close(DB); 
	open(DB,"$vote_code/Log_2.cgi");@comlist2 = <DB>;close(DB); 
	$data_num1 = $comlist1[0];# 0行目に書き込み数
	$data_num2 = $comlist2[0];
	
	# 今回使うデータを得る＆次回書き込み先をセット
	# 書き換え数が多い方を採用
	if( $data_num1 > $data_num2 ){ #1のほうが多い
		$big_num = $data_num1 + 1; #次用に+1
		@comlist = @comlist1;
		$next_file = "Log_2.cgi";
	}else{
		$big_num = $data_num2 + 1;#次用に+1
		@comlist = @comlist2;
		$next_file = "Log_1.cgi";
	}
	

	$insertPos = -1;
	$x = 0;
	foreach $com (@comlist) {
		@pairs = split(/<>/,$com);
		if(@pairs[0] eq $FORM{'ID'}){ # IDと一致する行を探す
			$insertPos = $x;
		}
		$x += 1;
	}
	#print "insert = $insertPos<BR>";
	
	# ●格納データを作る(Dは将来用のダミーデータ)
	# pairs[8]、pairs[9]、が選択キャラとお気に入り、
	# 10、11が選択番号とコメント、12、13が……と続く
	$newtext = "$FORM{'ID'}<>".$ENV{'REMOTE_ADDR'}."<>". &gethost . "<>D<>D<>D<>D<>D<>$selected_chara<>".$FORM{'favorite'}."<>";
	# 各キャラコメント
	$newtext .= $main_message ."<>";
	
	
	# 数値を更新
	$comlist[0]	= "$big_num";
	
	# ●書き換え or 追記
	if($insertPos != -1){
		# もともとあったX行目を置き換える
		$comlist[$insertPos] = $newtext;
	}else{
		# 新規追加の場合は下に足す
		push (@comlist,"$newtext");
	}

	# 書き込む
	#print "AAAAAAA $vote_code/$next_file";
	open(DB,">$vote_code/$next_file") || print "error $vote_code/$next_file";
	eval 'flock(DB,2);';
	$count = 0;
	$mail_text = "人気投票データです。\n\n";
	foreach $com (@comlist){
		if($count == 0){
			print DB $com."\n";
		}
		# 2行目に空データが入りやすいので文字数が少ないなら入れない
		if($count >= 1 && length($com) >= 4 ){
			print DB $com."\n";
			$mail_text .= $com."\n";# メール用
		}
		$count += 1;
	}
	
	eval 'flock(DB,8);';close(DB);
	
	# 書き込みしたら一旦終了メッセージ
	$init_query = "VOTE=".$vote_code."&ID=".$user_id;
	
	# Cookie書き込みはContent-typeより前に行う必要がある
	# Cookie書き込み	(100日記憶)
	($secg,$ming,$hourg,$mdayg,$mong,$yearg,$wdayg,$ydayg,$isdstg) = gmtime(time + 100*24*60*60);
	$yearg += 1900;
	if ($secg  < 10) { $secg  = "0$secg";  }
	if ($ming  < 10) { $ming  = "0$ming";  }
	if ($hourg < 10) { $hourg = "0$hourg"; }
	if ($mdayg < 10) { $mdayg = "0$mdayg"; }
	$month = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')[$mong];
	$youbi = ('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')[$wdayg];
	$date_gmt = "$youbi, $mdayg\-$month\-$yearg $hourg:$ming:$secg GMT";
	
	# Cookie入れたら最初のContent-typeみたいなの入れなくても平気っぽい。これが最初になるので注意
	print "Set-Cookie: $vote_code=$user_id; expires=$date_gmt;\n\n";
	

# ヘッダ部は共通
print <<END_OF_DATA;
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<meta http-equiv="Pragma" content="no-cache">

<TITLE>人気投票ページ</TITLE>
<LINK REL="stylesheet" HREF="ryodan_ninki.css" TYPE="text/css">

END_OF_DATA
	
print <<END_OF_DATA;
<BR><BR><CENTER>
<B style="color:#f33;">投票内容が送信されました、本当にありがとうございます！<BR>
<BR>※このページをブックマークしておくと、時間がたっても後から内容を修正することができます<BR>
</B><BR>
<BR>
先ほどまでの入力内容を引き継いで修正をおこないたい方はこちらから！<BR>
↓<BR>
<a href="./$cgi_name?$init_query">【投票ページへ戻る】</a>
</CENTER>
END_OF_DATA

	# 5回ごとに送信
	if( ($big_num % 2) == 0 ){
		&send_mail("旅団世界人気投票ログ $big_num",$mail_text );
	}
	exit;  # POSTデータがあれば終了する
}





$user_id = "";

# GET内容はここで読み取る。必要なのは投票タイプコード
if ( $ENV{'QUERY_STRING'} ne "" ) {
	#print ">>>>>>>$ENV{'QUERY_STRING'}<<<<<<";
	@pairs = split(/&/, $ENV{'QUERY_STRING'} );
	foreach $pair (@pairs) {
		($sname, $value) = split(/=/, $pair);
		$value =~ tr/+/ /;	#	※基本のデコードはこの行
		$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		$value =~ s/\t/ /g;$value =~ s/\r/\n/g;
		$FORM_G{$sname} = $value;
	}
	
	$vote_code = $FORM_G{'VOTE'};
	$user_id = $FORM_G{'ID'};
}


if( $vote_code eq ""){
	print "<BR><BR><BR>ERROR：投票コードがありません。このエラーが表示される場合、すでに投票が終わっている場合がございます。";
	
	exit;

}


# ●HTML出力
{

	# クッキー取得
	$cook = $ENV{'HTTP_COOKIE'};

	# 該当の投票のユーザIDを取り出す
	#print "TEST >> クッキー→「$cook」<BR>";
	foreach ( split(/;/, $cook) ) {
		($key,$val) = split(/=/);
		$key =~ s/\s//g;
		$cook{$key} = $val;
	}
	# もしユーザIDが空ならクッキーから得る
	if( $user_id eq "" ){
		# 今の投票コードからユーザIDを得る	
		$user_id = $cook{ $vote_code } ;
	}
	
	
	# もしIDがあったらデータを読み込もうとする
	%LOAD_DATA;
	#print "▼ユーザIDは$user_id <BR>";
	if( $user_id ne "" ){
		#●ファイルの読み込み、比較
		open(DB,"$vote_code/Log_1.cgi");@comlist1 = <DB>;close(DB); 
		open(DB,"$vote_code/Log_2.cgi");@comlist2 = <DB>;close(DB); 
		$data_num1 = $comlist1[0];# 0行目に書き込み数
		$data_num2 = $comlist2[0];
		# 今回使うデータを得る＆次回書き込み先をセット
		# 書き換え数が多い方を採用
		if( $data_num1 > $data_num2 ){ #1のほうが多い
			$big_num = $data_num1 + 1; #次用に+1
			@comlist = @comlist1;
			$next_file = "Log_2.cgi";
		}else{
			$big_num = $data_num2 + 1;#次用に+1
			@comlist = @comlist2;
			$next_file = "Log_1.cgi";
		}
		
		$insertPos = -1;
		$x = 0;
		foreach $com (@comlist) {
			@pairs = split(/<>/,$com);
			if(@pairs[0] eq $user_id){ # IDと一致する行を探す
				$insertPos = $x;
				last;
			}
			$x += 1;
		}
		#print "INSERT = $insertPos<BR>";
		#print $comlist[$insertPos];
		# IDが見つかったら読み込む。
		if( $insertPos != -1 ){
			# 選択済みキャラ
			@pairs = split(/<>/,$comlist[$insertPos]);
			@selected = split(/,/,$pairs[8]);
			foreach $sel(@selected){
				$name = "chara_".$sel;
				$LOAD_DATA{$name} = "checked";
				#print "★$name = OK<BR>";
			}
			$favorite = $pairs[9];
			
			# 各メッセージへのコメント読み込み
			for( $i = 10 ; $i<99; $i += 2){
				$j = $i + 1;
				if( $pairs[$i] eq ""){ last; } #何も入ってなかったら終了
				$name = "text" . $pairs[$i];
				
				$pairs[$j] =~ s/&lt;/</g;
				$pairs[$j] =~ s/&gt;/>/g;
				$pairs[$j] =~ s/<BR>/\n/g;# 改行コードを戻す
				$LOAD_DATA{$name} = $pairs[$j];
				#print "$i($pairs[$i]) = $j($LOAD_DATA{$pairs[$i]})<BR>";
				
			}
		}
		
	}
	

	# ★IDが不明ならランダムIDを生成してhiddenに入れておく（送信時のGET文に入れる）
	if( $user_id eq "" ){
		$user_id = &rand_str(8,"a-zA-Z0-9");
	}
	
	# フォームの送信クエリーをここで指定
	$init_query = "VOTE=".$vote_code."&ID=".$user_id;
	
	# VOTEコードに応じたキャラクター一覧データを読み込む
	open(DB,"$vote_code/chara_list.cgi");@dlist = <DB>;close(DB); 
	# 人数をカウント
	$chara_count = 0;
	foreach $data(@dlist) {
		( $c_num,$c_name,$imgfile,$detail ) = split(/<>/,$data);
		if($c_num >= 1){
			$chara_count += 1;
		}
		if($c_num eq "TITLE"){
			$title = $c_name;
		}
	}
# ヘッダ

print "Content-type: text/html; charset=utf-8\n\n";
# ヘッダ部は共通
print <<END_OF_DATA;
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<meta http-equiv="Pragma" content="no-cache">

<TITLE>人気投票ページ</TITLE>
<LINK REL="stylesheet" HREF="ryodan_ninki.css" TYPE="text/css">

END_OF_DATA

print <<END_OF_DATA;
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>

<STYLE TYPE="text/css">
<!--
	body{
		
		margin-left:1em;
		margin-right:1em;
	}
-->
</STYLE>

<SCRIPT language=JavaScript>
<!--
// ●一覧キャラが選択された

function click_chara( input ){
	tname = "chara_check" + input;
	tname_r = "chara_f" + input;
	
	//alert(tname);
	// オンオフ切り替え
	document.getElementById(tname).checked = true - document.getElementById(tname).checked;
	// 消えたならラジオボタンをオフ
	if( document.getElementById(tname).checked == false ){
		document.getElementById(tname_r).checked = false;
	}else{
		//オンになってもし5つあったら次のを消す
		var on_count = 0;
		for (  var i = 1;  i <= $chara_count;  i++  ) {
			tname1 = "chara_check" + i;
			if( document.getElementById(tname1).checked == true ){
				on_count += 1;
			}
		}
		if( on_count > 5){
			i = input;
			while (1) {
				i += 1;
				i = i % ($chara_count+1);
				if( i == 0 ){i = 1;}
				tname1 = "chara_check" + i;
				if( i != input){
					if(document.getElementById(tname1).checked == true ){
						document.getElementById(tname1).checked = false;
						break;
					}
				}
			}
		}
	}
	// 描画更新
	all_redraw();
}

// ●お気に入りキャラが選択された
function click_fav_chara( input ){
	tname = "chara_f" + input;
	// オンオフ切り替え。ラジオボタンは1つしか反応しない
	document.getElementById(tname).checked = true;

	// 描画更新
	all_redraw();
}


// ●描画更新
function all_redraw(){
	// 全て表示する処理
	\$('#baseform').css('display', 'block');
	\$('#noform').css('display', 'none');

	if( window.parent.screen.width >= 1024 ){
		// 画面サイズが横1024以上なら「PC版」を初期値にする
			\$('body').css('font-size', '10px');
			\$('body').css('font-size', '1em');
	}else{
			\$('body').css('font-size', '19px');
			\$('body').css('font-size', '1.9em');
	}
	
	// チェックボックスを見て欄とお気に入りキャラの表示非表示切り替え
	var on_count = 0;
	for (  var i = 1;  i <= $chara_count;  i++  ) {
		tname1 = "chara_check" + i;
		tname2 = "chara_f" + i;
		// 通常キャラ選択がオン
		name1 = "#chara_m" + i;
		name2 = "#chara_mc" + i;
		name3 = "#fav" + i;
		name_box = "#box" + i;
		if( document.getElementById(tname1).checked == true ){
			\$(name1).css('filter', 'brightness(100\%)');
			\$(name2).css('display', 'block');
			\$(name3).css('display', 'block');
			\$(name_box).css('display', 'block');
			\$(name1).css('box-shadow', '0px 0px 5px 5px #9F9');
			on_count += 1;
		}else{
			\$(name1).css('filter', 'brightness(40\%)');
			\$(name2).css('display', 'none');
			\$(name3).css('display', 'none');
			\$(name_box).css('display', 'none');
			\$(name1).css('box-shadow', '0px 0px 0px 0px #FFF');
		}
		
		// ラジオボタンがオンならお気に入りキャラにチェック入れる
		name1 = "#chara_mf" + i;
		name2 = "#chara_mfc" + i;
		name3 = "#chara_mfi" + i;
		if( document.getElementById(tname2).checked == true){
			
			\$(name2).css('filter', 'brightness(100\%)');
			\$(name3).css('display', 'block');
			\$(name2).css('box-shadow', '0px 0px 10px 10px #f33');
		}else{
			\$(name2).css('filter', 'brightness(50\%)');
			\$(name3).css('display', 'none');
			\$(name2).css('box-shadow', '0px 0px 0px 0px #FFF');
		
		}
	}
	
	// 1つもカウントがなければ「キャラクターを選ぶとここに表示されます」が出る
	name1 = "#hint1";
	name2 = "#hint2";
	if( on_count == 0 ){
		\$(name1).css('display', 'block');
		\$(name2).css('display', 'block');
		
	}else{
		\$(name1).css('display', 'none');
		\$(name2).css('display', 'none');
		
	}
}

// -->
</SCRIPT>
</HEAD>
<BODY onLoad="all_redraw()">

$post_message

<BR><BR>
<TABLE class="gradientA" cellpadding="3" cellspacing="1" width="100%" style="min-height:2em;">
<TBODY><TR>
<TD colspan="1" align="center" style="vertical-align:middle;">
<span style=" text-shadow: 0 0 7px #AAAABB, 0 0 7px #AAAABB; line-height:170%;color:#FFF;">$title<BR>人気投票ページ</FONT> </TD>
</TR>
</TBODY></TABLE>
<BR>
<SMALL>　リプレイを読んでくださってありがとうございます！<BR>
　ここでは登場人物たちに投票をおこなうことができます。<BR>
　<BR>
　もし一定以上の投票が集まれば、次巻や次話で結果を公開する予定です。あなたの応援したいキャラクターにぜひ一票を！
</SMALL>

<div id="noform">
<noscript>
<CENTER>
<BR><BR><font color="#f44"><BIG>投票に参加される場合は「JavaScript」を「オン」にしてくださる必要がございます。<BR></BIG></font>
</CENTER>
</noscript>
</div>

<FORM method="POST" action="./$cgi_name?$init_query" id="baseform" style="display:none;">

<INPUT type="hidden" name="VOTE" value="$vote_code">
<INPUT type="hidden" name="ID" value="$user_id">
<HR><BR>
<B>【好きなキャラを最大5人まで選んでください】</B>
END_OF_DATA



# ●読み込んだデータ分の枠（最初は見えない）と顔のHTMLを表示する。
#@dlist = ("1<>リゼット<>chara01.png<>PC:半獣人の騎士<>","2<>ブリンク<>chara02.png<>PC:演じる魔術師<>");

foreach $data(@dlist) {

( $c_num,$c_name,$imgfile,$detail ) = split(/<>/,$data);

if($c_num >= 1){
	# 1以上の数値があった場合だけ進む
}else{
	next;
}

# 見えないチェックボックスとお気に入りラジオボックス欄
$favcheck = "";
if( $favorite == $c_num ){
	$favcheck = "checked";
}

$checkbox_list .= <<END_OF_DATA;
<div style="display:none;">
<INPUT type="checkbox" name="chara_$c_num" id="chara_check$c_num" $LOAD_DATA{"chara_$c_num"}>
<INPUT type="radio" id="chara_f$c_num" name="favorite" value="$c_num" $favcheck>
</div>
END_OF_DATA


# 顔リスト、これをクリックすると選択状態が切り替わる
$face_list .= <<END_OF_DATA;
<TABLE style="float:left; width:20%;"><TR><TD align="center">
<div style="position:relative; line-height:0.8em;">
<a class="selectbase" href="javascript:click_chara($c_num);">
<img src="face_image/$imgfile" id="chara_m$c_num" style="filter: brightness(40%); width:100%;border-radius:1em;">
<div style="position:absolute;top:0%;left:0%;width:25%;display:none;" id="chara_mc$c_num" ><img src="face_image/icon_on.png" style="width:100%;"></div><BR>
<SMALL><SMALL><B>$c_name</B><BR><SMALL>$detail</SMALL></SMALL></SMALL></a>
</div></TD></TR></TABLE>
END_OF_DATA

if(($c_num%5)== 0){
	$face_list .= "<BR clear='left'>";
}

# 入力欄
$inittext = $LOAD_DATA{"text$c_num"};
#print "$inittext<BR><BR>";

$box_list .= <<END_OF_DATA;
<div id="box$c_num">
<TABLE border="0" >
  <TBODY>
    <TR>
      <TD style="width:20%;"><img src="face_image/$imgfile" style="width:90%;"></TD>
      <TD><SMALL>$c_nameへ<SMALL style="color:#99A;">（空欄でも可）</SMALL></SMALL><BR><TEXTAREA rows="3" name="text$c_num" placeholder="$c_nameへの応援メッセージやご感想があればここへどうぞ！" style="width:90%;border: 2px solid #059;border-radius: 1em;padding: 0.5em;font-size:1.2em;">$inittext</TEXTAREA></TD>
    </TR>
  </TBODY>
</TABLE>
</div>
END_OF_DATA


# 選択済みならJSでお気に入りリストに追加して選ばせる。
$favface_list .= <<END_OF_DATA;
<div style="position:relative; width:22%; float:left;" id="fav$c_num">
<TABLE style="float:left; width:95%;"><TR><TD align="center">
<a class="selectbase" id="chara_mf$c_num" href="javascript:click_fav_chara($c_num);">
<img src="face_image/$imgfile" width="100%" id="chara_mfc$c_num" style="border-radius:2em;"><div id="chara_mfi$c_num" style="position:absolute;top:10%;left:10%;width:20%;display:none;"><img src="face_image/icon_fav.png" style="width:100%;"></div><BR>
<SMALL><SMALL><B>$c_name</B></SMALL></SMALL></a>
</TD></TR></TABLE></div>
END_OF_DATA
}

if(($c_num%5)== 0){
	$favface_list .= "<BR clear='left'>";
}
# ここでHTML生成終了



# ●表示する　テーブルにclear: left;
print $checkbox_list."<BR><BR>".$face_list."<BR clear='left'><HR><BR>";

# ▼コメント欄
print <<END_OF_DATA;
<B>【応援コメントを書く】</B><BR>
　もし応援のコメントを送りたいキャラクターがいればこちらからどうぞ！　「かっこいい！」なんて一言でもはげみになります（全て空欄でも大丈夫ですよ）<BR>　
<div style='border:1px #ddddff solid; padding:9px;'>
<div id="hint1">
<CENTER>
<SMALL><SMALL>投票したいキャラクターを選択すると、ここに「応援コメント入力欄」が表示されます。</SMALL></SMALL>
</CENTER>
</div>
END_OF_DATA


print "".$box_list;

# ▼コメント欄
print <<END_OF_DATA;
</div>
<BR><HR><BR>
<B>【お気に入りを選ぶ】</B><BR>
　あなたのお気に入りの<B style="color:#f44;">キャラクターを1人</B>選んでください！<BR>
　<SMALL>（人気投票のポイントが3倍になります）</SMALL><BR><BR>

<div id="hint2">
<div style='border:1px #ddddff solid; padding:9px;'>
<CENTER>
<SMALL><SMALL>投票したいキャラクターを選択すると、ここで「お気に入り」が選べるようになります。</SMALL></SMALL>
</CENTER>
</div>
</div>

END_OF_DATA

print "".$favface_list ,"";

print <<END_OF_DATA;
<BR clear='left'>
<BR><HR><BR><CENTER>
<font color="#F44">　※この「送信」ボタンを押すと投票内容が保存されます。後で続けて内容を変更することも可能です。</font><BR><BR><BR>
<INPUT type="submit" value="送信（保存）">
</CENTER>
<BR><BR><BR><HR><BR><BR><BR><BR>　　　
END_OF_DATA

# フッター
print <<END_OF_DATA;
</FORM>
</BODY></HTML>
END_OF_DATA

}




# ランダム文字列生成　my $rand_str = &rand_str(8,"a-zA-Z0-9"); で使う
sub rand_str{	
	my ($str_len,$char_type) = @_;
	my @chars;

	#####　各文字種の指定あれば配列に追加
	push @chars, ('a'..'z') if $char_type =~ /a-z/;
	push @chars, ('A'..'Z') if $char_type =~ /A-Z/;
	push @chars, (0..9) if $char_type =~ /0-9/;
	my $total = @chars;

	my $rand_str = "";
	#####　randとintを用いて生成
	$rand_str .= $chars[int(rand($total))] for (1..$str_len);

	return $rand_str;
	
}


sub gethost{
	local($proxycheck,$host,$host2);
	$proxycheck=0;
	#$proxycheck=1 if($ENV{'HTTP_VIA'});
	$proxycheck=1 if($ENV{'HTTP_X_FORWARDED_FOR'});
	$proxycheck=1 if($ENV{'HTTP_FORWARDED'});
	$proxycheck=1 if($ENV{'HTTP_USER_AGENT'}=~/via/i);
	$proxycheck=1 if($ENV{'HTTP_SP_HOST'});
	$proxycheck=1 if($ENV{'HTTP_CLIENT_IP'});
	$host=$ENV{'REMOTE_HOST'};
  $addr= $ENV{'REMOTE_ADDR'};
  if ($host eq $addr) {$host = gethostbyaddr(pack('C4',split(/\./,$host)),2) || $addr;}
	if( $ENV{'HTTP_VIA'}=~s/.*\s(\d+)\.(\d+)\.(\d+)\.(\d+)/$1.$2.$3.$4/){
		$host2=$ENV{'HTTP_VIA'};$proxycheck=0;}
	if($ENV{'HTTP_X_FORWARDED_FOR'}=~s/^(\d+)\.(\d+)\.(\d+)\.(\d+)(\D*).*/$1.$2.$3.$4/){
		$host2=$ENV{'HTTP_X_FORWARDED_FOR'};$proxycheck=0;}
	if($ENV{'HTTP_FORWARDED'}=~s/.*\s(\d+)\.(\d+)\.(\d+)\.(\d+)/$1.$2.$3.$4/){
		$host2=$ENV{'HTTP_FORWARDED'};$proxycheck=0;}
	if($ENV{'HTTP_SP_HOST'}=~s/.*\s(\d+)\.(\d+)\.(\d+)\.(\d+)/$1.$2.$3.$4/){
		$host2=$ENV{'HTTP_SP_HOST'};$proxycheck=0;}
	if($ENV{'HTTP_CLIENT_IP'}=~s/.*\s(\d+)\.(\d+)\.(\d+)\.(\d+)/$1.$2.$3.$4/){
		$host2=$ENV{'HTTP_CLIENT_IP'};$proxycheck=0;}
	$host2 = &nslook($host2) if($host2=~/([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)/);
	$host .="[$host2]" if($host2);
	if ($proxycheck){$host .="(proxy)";}
	return $host;
}



# メール送信（タイトル・内容）を引数に指定
sub send_mail {
local ($mailsub, $mailmsg) = @_;

#print "$mailsub\n～000000000$mailmsg";

$sendmail = "/usr/sbin/sendmail";


# 記事の改行・タグを復元
$mailmsg =~ s/<br>/\n/ig;
$mailmsg =~ s/&lt;/</g;
$mailmsg =~ s/&gt;/>/g;
$mailmsg =~ s/&quot;/\"/g;
$mailmsg =~ s/&#39;/\'/g;
$mailmsg =~ s/&amp;/&/g;



# JISコード変換、はいらなかった。下の文字コードUTF-8にすれば問題ない
#&jcode'convert(*mailsub,'jis');	
#&jcode'convert(*mailmsg,'jis');	

# 送信処理
open(MAIL,"| $sendmail -t") || &error("メール送信に失敗しました");
print MAIL "To: $mailto\n";
print MAIL "From: $mail\n";
print MAIL "Subject: $mailsub\n";
print MAIL "MIME-Version: 1.0\n";
#print MAIL "Content-type: text/plain; charset=ISO-2022-JP\n";
print MAIL "Content-type: text/plain; charset=UTF-8\n"; # UTF-8なのでこれを使う
print MAIL "Content-Transfer-Encoding: 7bit\n";
print MAIL "X-Mailer: silversecond auto mailer\n";
print MAIL "$mailmsg\n";
close(MAIL);



}



sub error {
	local($err) = @_;
	local($msg);

	$msg  = "Content-type: text/html\n";
	$msg .= "\n";
	$msg .= "<html>\n";
	$msg .= "<head>\n";
	$msg .= "<meta http-equiv=\"Content-type\" content=\"text/html; charset=EUC-JP\">\n";
	$msg .= "<title>メール送信結果</title>\n";
	$msg .= "</head>\n";
	$msg .= "<body>\n";
	$msg .= "<h1>メール送信結果</h1>\n";
	$msg .= "<hr>\n";
	$msg .= "<p>$err</p>\n";
	$msg .= "<p>ブラウザの [戻る] ボタンで戻ってください。</p>\n";
	$msg .= "<hr>\n";
	$msg .= "<p align=\"right\"><font size=\"2\" color=\"#ffffcc\"><a href=\"http://www.ablenet.jp/\" style=\"color:#999;text-decoration: none;\">Powered by Ablenet</a></font>\n";
	$msg .= "</body>\n";
	$msg .= "</html>\n";

	&jcode'convert(*msg, "euc");

	print $msg;

	exit(0);
}