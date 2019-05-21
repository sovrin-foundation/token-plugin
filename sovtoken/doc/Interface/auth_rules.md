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
    <th>XFER_PUBLIC</th>
    <th>ADD</th>
    <th>*</th>
    <th>*</th>
    <th>*</th>
    <th>Anyone</th>
    <th>Making payment operation</th>
  </tr>

  <tr>
    <th>MINT_PUBLIC</th>
    <th>ADD</th>
    <th>*</th>
    <th>*</th>
    <th>*</th>
    <th>3 TRUSTEEs</th>
    <th>Token's minting</th>
  </tr>
