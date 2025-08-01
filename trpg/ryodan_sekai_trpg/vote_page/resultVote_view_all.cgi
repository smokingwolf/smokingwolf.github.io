#!/usr/local/bin/perl
use CGI::Carp qw(fatalsToBrowser);

# ●パラメータ設定
@IDlist=("webReplay01","Replay01_ABIYW6GLZ");

$script_name = (split "/",$ENV{"SCRIPT_NAME"})[$self-1];

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
	
	
	
	$pass = $FORM{'pass'};
	
	print "$pass";
	if( $pass ne "katakata" ){
		print "Content-type: text/html; charset=utf-8\n\n";
		print "パスワードが違います！　ログを記録しました。";
		exit;
	}
	
}else{ #POSTがなかったらパス入力画面
	print "Content-type: text/html; charset=utf-8\n\n";
	print "<FORM method=\"POST\" action=\"$script_name\">パスワード<input type=\"text\" name=\"pass\" size=\"10\"></input>";
	print "<input type=\"submit\">";
	print "</FORM>";
	exit;

}



print "Content-type: text/html; charset=utf-8\n\n";
print <<END_OF_TEXT;
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
END_OF_TEXT

@clist = ();
foreach $id (@IDlist){
	open(IN,"$id/chara_list.cgi");
	@charalist=<IN>;
	close(IN);
	
	# キャラ情報を読み込み
	$x = 0;
	foreach $chara(@charalist){
		if($chara =~ /<>/ ){
			@cpair = split(/<>/,$chara);
			$clist[$cpair[0]] = $cpair[1]; # ID ・ 名前
		}
	}

	#●ファイルの読み込み、比較
	open(DB,"$id/Log_1.cgi");@comlist1 = <DB>;close(DB); 
	open(DB,"$id/Log_2.cgi");@comlist2 = <DB>;close(DB); 
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

	# データを取り出して放り込む
	$x = 0;
	@clistcom = ();

	foreach $com (@comlist) {
		# 1行ずつデータを取り出す
		@pairs = split(/<>/,$com);
		# ●格納データを読む
		# pairs[8]、pairs[9]、が選択キャラとお気に入り、
		# 10、11が選択番号とコメント、12、13が……と続く
		@selected = split(/,/,$pairs[8]);
		foreach $sel(@selected){
		}
		$favorite = $pairs[9];
		# 各メッセージへのコメント読み込み
		for( $i = 10 ; $i<99; $i += 2){
			$j = $i + 1;
			if( $pairs[$i] eq ""){ last; } #何も入ってなかったら終了
			if( $pairs[$j] eq ""){ next; } #コメントなしなら次
			
			$pairs[$j] =~ s/&lt;/</g;
			$pairs[$j] =~ s/&gt;/>/g;
			#$pairs[$j] =~ s/<BR>/\n/g;# 改行コードを戻す
			$clistcom[$pairs[$i]] .= "●".$pairs[$j]."<BR>";
			#print "$i($pairs[$i]) = $j($LOAD_DATA{$pairs[$i]})<BR>";
			
		}
	}

	for( $i = 0 ; $i<99; $i += 1){
		if($clist[$i] ne ""){
			print "<B>$clist[$i]</B>へのコメント<BR>".$clistcom[$i];
			print "<BR><HR><BR>";
		}
	}

}

exit;
