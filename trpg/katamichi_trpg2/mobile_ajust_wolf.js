window.addEventListener('DOMContentLoaded', function() {
    // 実行したい処理を書く
    init_mode();
})


function init_mode(){
	if( window.parent.screen.width >= 1024 ){
		// 画面サイズが横1024以上なら「PC版」を初期値にする
		$('body').css('font-size', '0.9em');
		/*alert(  window.parent.screen.width + "A" ); */
	}
	else
	{
		// それ以外ならスマホ版を初期値にする
		$('body').css('font-size', '1.2em');
		$('.white').css('font-size', '0.8em');
		
		/*alert(  window.parent.screen.width + "B" ); */
	}
}