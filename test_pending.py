from challan_workflow.services.redirections import handle_post_redirect


challan_no = "WB120268250704171258"

if __name__ == "__main__":
    handle_post_redirect(
        challan_no=challan_no,
        method="POST",
        url="https://vahan.parivahan.gov.in/eTransPgi/checkfailtransaction", 
        data={
            "encdata": "867a6181af0aea2cc3570016d257debce8e365843263a0a48c3b1d94342fd0bc189f9ed336e65a354b67b5ad62a6d863eecf33060fb571c4722eb33445148cfe4278e8c5ff1692a661f0735d5c83215c697ce7d5a9ca48f9f8c3159a1536f64c6463a04654aa44cc585e474626b6659717344abb7fdb7e1bec443ac5dab8b24c1d271814fd174f7efda3e96fb706ba7539ac59453aa7ac8d1c0ef3e4555ebb0e"
        }
    )