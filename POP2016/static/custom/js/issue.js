/**
 * Created by Huxing on 2016/3/4.
 */

$(function(){
    /*
    $(".create-form").on('submit', function(e){
        e.preventDefault();
        var issue_type = $("select[name='issue-type']").val().trim();
        var issue_head = $("input[name='issue-head']").val().trim();
        var issue_body = $("textarea[name='issue-body']").val().trim();
        var email = $("input[name='email']").val().trim();
        var btn = $(".create-btn").button('loading');
        $.post("create", {type: issue_type, head: issue_head, body: issue_body, email: email}, function(data){
            if(data.code == 1){
                alert(data.msg);
            }
            else{
                window.location.reload();
            }
        }, "json");
    });*/

    $(".add-communication").on('submit', function(e){
            e.preventDefault();
            var content = $("textarea[name='content']").val().trim();
            var url = window.location.href;
            var args = url.substr(url.indexOf("?"),url.length);
            var arg = args.split("&");
            var issue_id;
            if(arg.length>1)
            {
                issue_id = arg[1]
            }
            else{
                issue_id = arg[0]
            }
            issue_id = issue_id.split("=")[1];
            $.post('/addcommunication', {issueid:issue_id, content:content}, function(data){
                if(data.code == 1){
                    alert(data.msg);
                }
                else{
                    window.location.replace("/detail?issueid="+issue_id)
                }
            }, "json");
        });
    /*
    $("#delete").click(function(){
        var issue_id = $(this).parent().parent().attr('id');
        $.post('/delete', {issueid: issue_id}, function(data){
            if(data.code==1){
                alert(data.msg);
            }
            else{
                window.location.reload()
            }
        }, "json");
    });
    $("#detail").click(function(){
       var issue_id = $(this).parent().parent().attr("id");
        $.post('/detail', {issueid: issue_id}, function(data){
            if(data.code==1){
                alert(data.msg);
            }
        }, "json");
    });
    $("#check").click(function(){
        var issue_id = $(this).parent().parent().attr('id');
        $.post('/check', {issueid: issue_id}, function(data){
            if(data.code==1){
                alert(data.msg);
            }
            else{
                window.location.reload()
            }
        }, "json");
    });
    */
});