# Tokens related auth_rules
The next authorization rules extend default auth_map from indy-node ([auth_map](https://github.com/hyperledger/indy-node/blob/master/docs/source/add-node.md))
<table class="tg">
  <tr>
    <td>Transaction type</td>
    <td>Action</td>
    <td>Field</td>
    <td>Previous value</td>
    <td>New value</td>
    <td>Who can</td>
    <td>Description</td>
  </tr>

  <tr>
    <td>XFER_PUBLIC</td>
    <td>ADD</td>
    <td>*</td>
    <td>*</td>
    <td>*</td>
    <td>Anyone</td>
    <td>Making payment operation</td>
  </tr>

  <tr>
    <td>MINT_PUBLIC</td>
    <td>ADD</td>
    <td>*</td>
    <td>*</td>
    <td>*</td>
    <td>3 TRUSTEEs</td>
    <td>Token's minting</td>
  </tr>
