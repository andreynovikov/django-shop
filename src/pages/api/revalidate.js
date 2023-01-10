export default async function handler(req, res) {
    if (req.body?.secret !== process.env.REVALIDATION_TOKEN) {
        return res.status(401).json({ message: 'Invalid token' })
    }

    if (!!!req.body.model || !!!req.body.pk) {
        return res.status(400).json({ message: 'Parameters missing' })
    }

    try {
        switch (req.body.model) {
            case 'category':
                await res.revalidate(`/catalog/${req.body.path}/`);
                break;
            case 'product':
                await res.revalidate(`/products/${req.body.code}/`);
                break;
            case 'page':
                await res.revalidate(`/pages${req.body.uri}`);
                break;
        default:
            return res.json({ revalidated: false });
        }
        return res.json({ revalidated: true });
    } catch (err) {
        // If there was an error, Next.js will continue
        // to show the last successfully generated page
        console.error(err);
        return res.status(500).send('Revalidation error');
    }
}
