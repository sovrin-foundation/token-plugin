# Tokens related auth_rules
The next authorization rules extend default auth_map from indy-node ([auth_map](https://github.com/hyperledger/indy-node/blob/master/docs/source/add-node.md))
<table class="tg">
  <tr>
    <th>Transaction type</th>
    <th>Action</th>
    <th>Field</th>
    <th>Previous value</th>
    <th>New value</th>
    <th>Who can</th>
    <th>Description</th>
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
